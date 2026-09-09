"""Create the local secret and the first named admin account, without overwriting either."""
from pathlib import Path
import os
import secrets
import sys

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
path = root / '.env'

if path.exists():
    print('.env already exists; no secret changed.')
else:
    path.write_text(f'TRUST_ENV=local\nTRUST_HMAC_KEY={secrets.token_urlsafe(40)}\n', encoding='utf-8')
    path.chmod(0o600)
    print('Created .env. Keep it private.')

from app.accounts import Directory
from app.config import Settings
from app.storage import Store, DEFAULT_ORG_ID

settings = Settings.from_env()
store = Store(settings.database, settings.report_ttl_days)
directory = Directory(store)

if directory.staff_list(DEFAULT_ORG_ID):
    print(f'\nStaff accounts already exist in {DEFAULT_ORG_ID}; none created.')
    print('Add another account with: python scripts/create_staff.py --help')
else:
    email = os.getenv('TRUST_ADMIN_EMAIL', 'admin@trust.local')
    password = secrets.token_urlsafe(15)
    account = directory.create_staff(DEFAULT_ORG_ID, email, 'Local administrator', password, 'admin')
    print('\n' + '=' * 72)
    print('FIRST ADMIN ACCOUNT — these values are shown once and are not stored in .env')
    print('=' * 72)
    print(f'  Email        {account["email"]}')
    print(f'  Password     {password}')
    print(f'  MFA secret   {account["totp_secret"]}')
    print(f'  Add to your authenticator app:\n    {account["provisioning_uri"]}')
    print('=' * 72)
    print('Sign-in requires the password AND a current 6-digit code from that app.')
    print('If you have no authenticator to hand, print a current code with:')
    print('  python scripts/create_staff.py --totp-code ' + account['totp_secret'])

print('\nStart: python -m uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8000 --no-access-log')
