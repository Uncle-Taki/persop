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


def request(port, path, token=None, body=None):
    headers = dict(token) if isinstance(token, dict) else ({'Authorization': 'Bearer ' + token} if token else {})
    data = json.dumps(body).encode() if body is not None else None
    if data is not None:
        headers['Content-Type'] = 'application/json'
    try:
        with urllib.request.urlopen(urllib.request.Request(f'http://127.0.0.1:{port}{path}', headers=headers, data=data), timeout=10) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as error:
        return error.code, error.read()


def wait_api(port, token):
    deadline = time.monotonic() + 120
    while time.monotonic() < deadline:
        try:
            ready_status, ready_body = request(port, '/ready')
            if ready_status == 200 and json.loads(ready_body)['data'].get('ready') is True and request(port, '/api/v1/operations/status', token)[0] in (200, 503):
                return
        except (OSError, TimeoutError, ValueError, KeyError, TypeError):
            pass
        time.sleep(2)
    raise RuntimeError('API did not recover before the deadline')


def login(port, values, password=None):
    payload = json.dumps({'username': values['BOOTSTRAP_ADMIN_USERNAME'], 'password': password or values['BOOTSTRAP_ADMIN_PASSWORD']}).encode()
    req = urllib.request.Request(f'http://127.0.0.1:{port}/api/v1/auth/login', data=payload, headers={'Content-Type':'application/json', 'Origin': f'http://127.0.0.1:{port}'})
    with urllib.request.urlopen(req, timeout=10) as response:
        body = json.load(response)['data']
        return {'Cookie': response.headers['Set-Cookie'].split(';')[0], 'X-CSRF-Token': body['csrf_token']}


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
        account_session = login(31880, source.values)
        assert request(31880, '/api/v1/session', account_session)[0] == 200
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
        old_status = request(31880, '/api/v1/operations/status', token)[0]
        assert old_status == 401, f'Old monitoring credential returned status {old_status}'
        assert request(31880, '/api/v1/operations/status', source.values['API_TOKEN'])[0] in (200, 503)
        assert request(31880, '/api/v1/session', source.values['API_TOKEN'])[0] == 401
        assert request(31880, '/api/v1/session', account_session)[0] == 200
        rotated_password = os.urandom(24).hex()
        assert request(31880, '/api/v1/me/password', account_session, {'current_password': source.values['BOOTSTRAP_ADMIN_PASSWORD'], 'password': rotated_password})[0] == 200
        assert request(31880, '/api/v1/session', account_session)[0] == 401
        account_session = login(31880, source.values, rotated_password)
        summary['checks']['password_change_revokes_sessions'] = 'passed'
        summary['checks']['monitoring_token_rotation_without_user_access'] = 'passed'
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
        restored_session = login(31881, source.values, rotated_password)
        assert request(31881, '/api/v1/session', restored_session)[0] == 200
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
        demo_session = login(31882, demo.values)
        assert request(31882, '/api/v1/session', demo_session)[0] == 200
        assert int(demo.sql("SELECT count(*) FROM products WHERE category='healthcare'")) == 1
        deadline = time.monotonic() + 90
        while int(demo.sql('SELECT count(*) FROM offers')) == 0 and time.monotonic() < deadline:
            time.sleep(2)
        assert int(demo.sql("SELECT count(*) FROM offers WHERE product_id='22222222-2222-2222-2222-222222222226' AND price_amount=25000")) > 0
        # An offer alone could come from deterministic fallback. Require persisted
        # evidence that the worker actually called the local HTTP provider.
        assert int(demo.mongo("db.getSiblingDB('perso_raw').llm_extractions.countDocuments({model_name:'openai-compatible (perso-healthcare-mock)'})")) > 0
        assert demo.sql('SELECT count(*) FROM outbound_messages') == b'0'
        summary['checks']['healthcare_worker_http_mock_and_no_outreach'] = 'passed'
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
