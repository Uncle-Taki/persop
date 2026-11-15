#!/usr/bin/env python3
"""Generate private local credentials without printing them or overwriting a file."""
import argparse
import os
import secrets
from pathlib import Path
parser=argparse.ArgumentParser()
parser.add_argument('--demo',action='store_true',help='Explicit mock Telegram data, no real account')
args=parser.parse_args()
path=Path(__file__).resolve().parents[1]/'.env'
lines={
 'ENVIRONMENT':'development' if args.demo else 'production',
 'API_TOKEN':secrets.token_hex(32),
 'POSTGRES_PASSWORD':secrets.token_hex(24),
 'MONGO_ROOT_PASSWORD':secrets.token_hex(24),
 'MONGO_APP_PASSWORD':secrets.token_hex(24),
 'REDIS_PASSWORD':secrets.token_hex(24),
 'TELEGRAM_GATEWAY_TOKEN':secrets.token_hex(32),
 'TELEGRAM_SESSION_STORAGE_KEY':secrets.token_hex(32),
 'TELEGRAM_APP_ID':'0','TELEGRAM_APP_HASH':'','TELEGRAM_PHONE_NUMBER':'',
 'TELEGRAM_MOCK_MODE':'true' if args.demo else 'false','LLM_ENABLED':'false','OUTREACH_ENABLED':'false',
 'RETENTION_DAYS':'0','FRONTEND_PORT':'3000',
}
try:
 fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
except FileExistsError:
 raise SystemExit('.env already exists; preserved without changes.')
with os.fdopen(fd,'w') as output:output.write('\n'.join(f'{k}={v}' for k,v in lines.items())+'\n')
print('Created .env with private credentials. Enter API_TOKEN in the browser. Never commit this file.')
