#!/usr/bin/env python3
"""Generate private local credentials without printing them or overwriting a file."""
import argparse
import os
import secrets
import uuid
from pathlib import Path


def create_environment(path: Path, demo: bool = False) -> None:
    values = {
        'ENVIRONMENT': 'development' if demo else 'production',
        'BOOTSTRAP_ADMIN_USERNAME': 'owner',
        'BOOTSTRAP_ADMIN_PASSWORD': secrets.token_hex(24),
        'AUTH_COOKIE_SECURE': 'false' if demo else 'true',
        'OPERATOR_USER_ID': '11111111-1111-1111-1111-111111111111' if demo else str(uuid.uuid4()),
        **{name: secrets.token_hex(32) for name in (
            'API_TOKEN', 'POSTGRES_PASSWORD', 'MONGO_ROOT_PASSWORD', 'MONGO_APP_PASSWORD',
            'REDIS_PASSWORD', 'TELEGRAM_GATEWAY_TOKEN', 'TELEGRAM_SESSION_STORAGE_KEY')},
        'TELEGRAM_APP_ID': '0', 'TELEGRAM_APP_HASH': '', 'TELEGRAM_PHONE_NUMBER': '',
        'TELEGRAM_MOCK_MODE': 'true' if demo else 'false',
        'LLM_ENABLED': 'false', 'OUTREACH_ENABLED': 'false',
        'RETENTION_DAYS': '0', 'FRONTEND_PORT': '3000',
    }
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w') as output:
        output.write('\n'.join(f'{key}={value}' for key, value in values.items()) + '\n')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--demo', action='store_true', help='Explicit mock data, no real account')
    parser.add_argument('--output', type=Path, default=Path(__file__).resolve().parents[1] / '.env')
    args = parser.parse_args()
    try:
        create_environment(args.output, args.demo)
    except FileExistsError:
        raise SystemExit('Environment file already exists; preserved without changes.')
    print('Created private environment file. Sign in with BOOTSTRAP_ADMIN_USERNAME and BOOTSTRAP_ADMIN_PASSWORD. API_TOKEN is monitoring-only. Never commit this file.')


if __name__ == '__main__':
    main()
