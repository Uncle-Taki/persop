#!/usr/bin/env python3
"""Check production configuration without displaying secret values."""
import argparse
import re
import stat
import uuid
from pathlib import Path

SECRET_KEYS = ('API_TOKEN', 'POSTGRES_PASSWORD', 'MONGO_ROOT_PASSWORD', 'MONGO_APP_PASSWORD',
               'REDIS_PASSWORD', 'TELEGRAM_GATEWAY_TOKEN', 'TELEGRAM_SESSION_STORAGE_KEY')


def read_environment(path):
    values = {}
    for line in path.read_text().splitlines():
        if line.strip() and not line.lstrip().startswith('#'):
            key, sep, value = line.partition('=')
            if not sep or key.strip() in values:
                raise ValueError('Invalid or duplicate environment assignment')
            values[key.strip()] = value.strip()
    return values


def validate(values, offline=False, public=False):
    errors = []
    for key in SECRET_KEYS:
        if not re.fullmatch(r'[A-Za-z0-9_-]{32,}', values.get(key, '')):
            errors.append(f'{key}: use an independently generated secret of at least 32 characters')
    if len({values.get(key) for key in SECRET_KEYS}) != len(SECRET_KEYS):
        errors.append('Secrets must be different from one another')
    try:
        owner = uuid.UUID(values.get('OPERATOR_USER_ID', ''))
        if owner.int == 0 or str(owner) == '11111111-1111-1111-1111-111111111111':
            raise ValueError()
    except ValueError:
        errors.append('OPERATOR_USER_ID: set a unique production workspace UUID')
    if values.get('ENVIRONMENT') != 'production' or values.get('TELEGRAM_MOCK_MODE') != 'false':
        errors.append('Production requires ENVIRONMENT=production and TELEGRAM_MOCK_MODE=false')
    if values.get('OUTREACH_ENABLED') != 'false':
        errors.append('Keep OUTREACH_ENABLED=false for preflight and the initial pilot')
    if values.get('LLM_ENABLED') != 'false':
        errors.append('Keep LLM_ENABLED=false until its optional verification gate passes')
    if not offline:
        if not values.get('TELEGRAM_APP_ID', '').isdigit() or int(values.get('TELEGRAM_APP_ID', '0')) <= 0:
            errors.append('TELEGRAM_APP_ID: enter your own application ID')
        if not re.fullmatch(r'[a-fA-F0-9]{32}', values.get('TELEGRAM_APP_HASH', '')):
            errors.append('TELEGRAM_APP_HASH: enter your own application hash')
        if not re.fullmatch(r'\+[0-9]{7,15}', values.get('TELEGRAM_PHONE_NUMBER', '')):
            errors.append('TELEGRAM_PHONE_NUMBER: use international format')
    if public and not re.fullmatch(r'(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}', values.get('PERSO_DOMAIN', '')):
        errors.append('PERSO_DOMAIN: enter the public hostname without scheme or path')
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--env-file', type=Path, default=Path('.env'))
    parser.add_argument('--offline', action='store_true', help='Skip real Telegram credential checks')
    parser.add_argument('--public', action='store_true', help='Require a public HTTPS hostname')
    args = parser.parse_args()
    try:
        values = read_environment(args.env_file)
        errors = validate(values, args.offline, args.public)
        if stat.S_IMODE(args.env_file.stat().st_mode) & 0o077:
            errors.append('Environment file must be accessible only to its owner (chmod 600)')
    except (OSError, ValueError):
        raise SystemExit('Could not read a valid private environment file')
    if errors:
        for error in errors:
            print(error)
        raise SystemExit(1)
    print('Configuration checks passed. Account authorization, HTTPS reachability and staging verification remain separate checks.')


if __name__ == '__main__':
    main()
