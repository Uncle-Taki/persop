#!/usr/bin/env python3
"""Run disposable container, persistence, token rotation and restore checks in CI."""
import importlib.util
import json
import os
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path
from backup import Deployment, backup, restore

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / 'artifacts'
spec = importlib.util.spec_from_file_location('setup_env', ROOT / 'scripts/setup-env.py')
setup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(setup)


def write_environment(path, values):
    with path.open('w') as output:
        os.chmod(path, 0o600)
        output.write(''.join(f'{key}={value}\n' for key, value in values.items()))


def request(port, path, token=None):
    headers = {'Authorization': 'Bearer ' + token} if token else {}
    try:
        with urllib.request.urlopen(urllib.request.Request(f'http://127.0.0.1:{port}{path}', headers=headers), timeout=10) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as error:
        return error.code, error.read()


def wait_api(port, token):
    deadline = time.monotonic() + 120
    while time.monotonic() < deadline:
        try:
            if request(port, '/api/v1/session', token)[0] == 200:
                return
        except (OSError, TimeoutError):
            pass
        time.sleep(2)
    raise RuntimeError('API did not recover before the deadline')


def main():
    ARTIFACTS.mkdir(exist_ok=True)
    summary = {'checks': {}, 'live_telegram': 'not exercised', 'image_ids': {}}
    source = target = demo = None
    start = time.monotonic()
    try:
        source_env = ARTIFACTS / '.env.rehearsal-source'
        setup.create_environment(source_env)
        source = Deployment('perso-release-source', source_env)
        source.values['FRONTEND_PORT'] = '31880'
        write_environment(source_env, source.values)
        source.run('config', '-q', stdout=subprocess.PIPE)
        source.run('build', 'backend-api', 'frontend')
        source.run('up', '-d', '--wait', 'postgres', 'mongodb', 'redis', 'backend-api', 'frontend', stdout=subprocess.PIPE)
        token = source.values['API_TOKEN']
        wait_api(31880, token)
        assert source.sql('SELECT count(*) FROM products') == b'0'
        assert source.sql('SELECT count(*) FROM telegram_sources') == b'0'
        assert request(31880, '/api/v1/products')[0] == 401
        assert request(31880, '/')[0] == 200
        summary['checks']['production_fresh_install_without_demo_data'] = 'passed'
        source.sql("INSERT INTO products(name,normalized_name,brand,model,category) VALUES('restore probe','restore probe','fixture','fixture','test')")
        source.mongo("db.getSiblingDB('perso_raw').restore_probe.insertOne({marker:'perso-restore-probe'})")
        source.run('run', '--rm', '--no-deps', '-T', '--entrypoint', 'sh', 'telegram-gateway', '-c', 'test "$(id -u)" = 10001 && umask 077 && printf synthetic-archive-fixture > /data/sessions/restore-probe.enc', stdout=subprocess.PIPE)
        # Verify the invalid and valid credentials against the same running deployment.
        source.values['API_TOKEN'] = os.urandom(32).hex()
        write_environment(source_env, source.values)
        source.run('up', '-d', '--no-deps', '--force-recreate', 'backend-api', stdout=subprocess.PIPE)
        wait_api(31880, source.values['API_TOKEN'])
        assert request(31880, '/api/v1/session', token)[0] == 401
        summary['checks']['api_token_rotation'] = 'passed'
        source.run('restart', 'postgres', 'mongodb', 'redis', stdout=subprocess.PIPE)
        wait_api(31880, source.values['API_TOKEN'])
        assert source.sql('SELECT count(*) FROM products') == b'1'
        assert source.mongo("db.getSiblingDB('perso_raw').restore_probe.countDocuments({marker:'perso-restore-probe'})") == b'1'
        summary['checks']['persistent_volumes_after_restart'] = 'passed'
        backup_dir = ARTIFACTS / 'private-rehearsal-backup'
        backup(source, backup_dir)
        target_env = ARTIFACTS / '.env.rehearsal-target'
        setup.create_environment(target_env)
        target = Deployment('perso-release-target', target_env)
        target.values.update({'TELEGRAM_SESSION_STORAGE_KEY': source.values['TELEGRAM_SESSION_STORAGE_KEY'],
                              'OPERATOR_USER_ID': source.values['OPERATOR_USER_ID'], 'FRONTEND_PORT': '31881'})
        write_environment(target_env, target.values)
        target.run('up', '-d', '--wait', 'postgres', 'mongodb', 'redis', stdout=subprocess.PIPE)
        restore(target, backup_dir)
        target.run('up', '-d', '--wait', 'backend-api', 'frontend', stdout=subprocess.PIPE)
        wait_api(31881, target.values['API_TOKEN'])
        assert target.sql('SELECT count(*) FROM products') == b'1'
        assert target.sql('SELECT count(*) FROM schema_migrations') == source.sql('SELECT count(*) FROM schema_migrations')
        assert target.mongo("db.getSiblingDB('perso_raw').restore_probe.countDocuments({marker:'perso-restore-probe'})") == b'1'
        target.run('run', '--rm', '--no-deps', '-T', '--entrypoint', 'sh', 'telegram-gateway', '-c', 'test "$(cat /data/sessions/restore-probe.enc)" = synthetic-archive-fixture && test "$(stat -c %u /data/sessions/restore-probe.enc)" = 10001', stdout=subprocess.PIPE)
        assert not target.running('telegram-gateway')
        summary['checks']['isolated_pg_mongo_session_restore'] = 'passed (synthetic session archive; real session authorization remains an operator check)'
        summary['recovery_elapsed_seconds'] = round(time.monotonic() - start, 2)
        # Reuse built images; demo still uses its own project, credentials and volumes.
        demo_env = ARTIFACTS / '.env.rehearsal-demo'
        setup.create_environment(demo_env, demo=True)
        demo = Deployment('perso-release-demo', demo_env)
        demo.values['FRONTEND_PORT'] = '31882'
        write_environment(demo_env, demo.values)
        demo.command += ['-f', str(ROOT / 'compose.demo.yaml')]
        demo.run('config', '-q', stdout=subprocess.PIPE)
        demo.run('up', '-d', '--build', '--wait', stdout=subprocess.PIPE)
        wait_api(31882, demo.values['API_TOKEN'])
        assert int(demo.sql('SELECT count(*) FROM products')) >= 5
        deadline = time.monotonic() + 90
        while int(demo.sql('SELECT count(*) FROM offers')) == 0 and time.monotonic() < deadline:
            time.sleep(2)
        assert int(demo.sql('SELECT count(*) FROM offers')) > 0
        backup(demo, ARTIFACTS / 'private-demo-backup')
        assert demo.running('telegram-gateway')
        summary['checks']['separate_demo_ingestion_and_gateway_backup_resume'] = 'passed'
        for service in ('backend-api', 'frontend'):
            summary['image_ids'][service] = source.run('images', '-q', service, stdout=subprocess.PIPE).stdout.decode().strip()
        summary['result'] = 'passed'
    except Exception as error:
        if isinstance(error, subprocess.CalledProcessError) and error.stderr:
            diagnostics = error.stderr.decode(errors='replace')
            for deployment in (source, target, demo):
                if deployment:
                    for value in deployment.values.values():
                        if len(value) >= 16:
                            diagnostics = diagnostics.replace(value, '[redacted]')
            (ARTIFACTS / 'container-diagnostics.txt').write_text(diagnostics)
            print(diagnostics)
        summary['result'] = 'failed; inspect the failed check and private Docker diagnostics'
        raise
    finally:
        (ARTIFACTS / 'container-rehearsal.json').write_text(json.dumps(summary, indent=2) + '\n')
        for deployment in (source, target, demo):
            if deployment:
                # These exact project names and volumes are disposable rehearsal resources.
                deployment.run('down', '-v', '--remove-orphans', stdout=subprocess.PIPE)


if __name__ == '__main__':
    main()
