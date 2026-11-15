#!/usr/bin/env python3
"""Back up or restore Perso into a different, empty Compose project."""
import argparse
import hashlib
import json
import os
import subprocess
import tarfile
from datetime import datetime, timezone
from pathlib import Path
from preflight import read_environment

ROOT = Path(__file__).resolve().parents[1]
FILES = ('postgres.dump', 'mongodb.archive', 'sessions.tar.gz')


class Deployment:
    def __init__(self, project, env_file):
        self.project = project
        self.env_file = env_file.resolve()
        self.values = read_environment(self.env_file)
        self.command = ['docker', 'compose', '--env-file', str(self.env_file), '-p', project, '-f', str(ROOT / 'compose.yaml')]

    def run(self, *args, **kwargs):
        return subprocess.run(self.command + list(args), check=True, cwd=ROOT, stderr=subprocess.PIPE, **kwargs)

    def running(self, service):
        return bool(self.run('ps', '--status', 'running', '-q', service, stdout=subprocess.PIPE).stdout.strip())

    def sql(self, text):
        return self.run('exec', '-T', 'postgres', 'psql', '-U', 'perso', '-d', 'perso_db', '-At', '-v', 'ON_ERROR_STOP=1', '-c', text, stdout=subprocess.PIPE).stdout.strip()

    def mongo(self, script):
        return self.run('exec', '-T', 'mongodb', 'sh', '-c', 'exec mongosh --quiet --username "$MONGO_INITDB_ROOT_USERNAME" --password "$MONGO_INITDB_ROOT_PASSWORD" --authenticationDatabase admin --eval "$1"', 'sh', script, stdout=subprocess.PIPE).stdout.strip()


def digest(path):
    with path.open('rb') as source:
        return hashlib.file_digest(source, 'sha256').hexdigest()


def session_key_digest(deployment):
    return hashlib.sha256(deployment.values['TELEGRAM_SESSION_STORAGE_KEY'].encode()).hexdigest()


def backup(deployment, directory):
    directory.mkdir(mode=0o700, parents=False, exist_ok=False)
    resume = [service for service in ('telegram-gateway', 'message-worker', 'backend-api') if deployment.running(service)]
    for service in resume:
        deployment.run('stop', service, stdout=subprocess.PIPE)
    try:
        commands = (
            ('exec', '-T', 'postgres', 'pg_dump', '-U', 'perso', '-d', 'perso_db', '-Fc'),
            ('exec', '-T', 'mongodb', 'sh', '-c', 'exec mongodump --username "$MONGO_INITDB_ROOT_USERNAME" --password "$MONGO_INITDB_ROOT_PASSWORD" --authenticationDatabase admin --db perso_raw --archive'),
            ('run', '--rm', '--no-deps', '-T', '--entrypoint', 'tar', 'telegram-gateway', '-C', '/data/sessions', '-czf', '-', '.'),
        )
        for name, command in zip(FILES, commands):
            with (directory / name).open('xb') as output:
                os.chmod(output.name, 0o600)
                deployment.run(*command, stdout=output)
            if not (directory / name).stat().st_size:
                raise ValueError('Backup produced an empty archive')
        manifest = {'version': 1, 'project': deployment.project, 'created_at': datetime.now(timezone.utc).isoformat(),
                    'session_key_sha256': session_key_digest(deployment),
                    'files': {name: digest(directory / name) for name in FILES}}
        with (directory / 'manifest.json').open('x') as output:
            os.chmod(output.name, 0o600)
            json.dump(manifest, output, indent=2)
    finally:
        if resume:
            deployment.run('up', '-d', '--no-deps', *reversed(resume), stdout=subprocess.PIPE)
    print('Backup completed. Encrypt and copy these archives to your private backup destination.')


def validate_archive(directory, manifest):
    if manifest.get('version') != 1:
        raise ValueError('Unsupported backup manifest')
    for name in FILES:
        if digest(directory / name) != manifest['files'][name]:
            raise ValueError('Archive checksum mismatch')
    with tarfile.open(directory / 'sessions.tar.gz') as archive:
        for member in archive.getmembers():
            path = Path(member.name)
            if path.is_absolute() or '..' in path.parts or not (member.isfile() or member.isdir()):
                raise ValueError('Unsafe session archive member')


def restore(deployment, directory):
    manifest = json.loads((directory / 'manifest.json').read_text())
    validate_archive(directory, manifest)
    if manifest['project'] == deployment.project:
        raise ValueError('Restore requires a different, empty project')
    if manifest['session_key_sha256'] != session_key_digest(deployment):
        raise ValueError('Restore environment must retain the original session encryption key')
    for service in ('telegram-gateway', 'backend-api', 'message-worker'):
        if deployment.running(service):
            raise ValueError('Restore target application services must be stopped')
    if deployment.sql("SELECT count(*) FROM pg_tables WHERE schemaname='public'") != b'0':
        raise ValueError('Restore target PostgreSQL database is not empty')
    if deployment.mongo("db.getSiblingDB('perso_raw').getCollectionNames().length") != b'0':
        raise ValueError('Restore target MongoDB database is not empty')
    deployment.run('run', '--rm', '--no-deps', '-T', '--entrypoint', 'sh', 'telegram-gateway', '-c', 'test -z "$(ls -A /data/sessions)"', stdout=subprocess.PIPE)
    commands = (
        ('exec', '-T', 'postgres', 'pg_restore', '--exit-on-error', '-U', 'perso', '-d', 'perso_db'),
        ('exec', '-T', 'mongodb', 'sh', '-c', 'exec mongorestore --username "$MONGO_INITDB_ROOT_USERNAME" --password "$MONGO_INITDB_ROOT_PASSWORD" --authenticationDatabase admin --archive --stopOnError'),
        ('run', '--rm', '--no-deps', '-T', '--entrypoint', 'tar', 'telegram-gateway', '-C', '/data/sessions', '-xzf', '-'),
    )
    for name, command in zip(FILES, commands):
        with (directory / name).open('rb') as source:
            deployment.run(*command, stdin=source, stdout=subprocess.PIPE)
    print('Restore completed with application services stopped. Verify counts/migrations before starting the API. Never start both copies of a real Telegram session.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['backup', 'restore'])
    parser.add_argument('--project', required=True)
    parser.add_argument('--env-file', type=Path, required=True)
    parser.add_argument('--directory', type=Path, required=True)
    args = parser.parse_args()
    try:
        deployment = Deployment(args.project, args.env_file)
        (backup if args.action == 'backup' else restore)(deployment, args.directory.resolve())
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError):
        raise SystemExit('Backup/restore failed; no success is recorded. Check private service diagnostics and target requirements. A partial restore must be discarded before retrying.')


if __name__ == '__main__':
    main()
