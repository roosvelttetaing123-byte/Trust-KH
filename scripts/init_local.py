"""Generate local secrets without overwriting an existing .env."""
from pathlib import Path
import secrets
root=Path(__file__).resolve().parents[1]
path=root/'.env'
if path.exists():
    print('.env already exists; no credentials changed.')
else:
    path.write_text('TRUST_ENV=local\n'+'\n'.join(f'{name}={secrets.token_urlsafe(40)}' for name in
                    ['TRUST_ADMIN_KEY','TRUST_PULSE_KEY','TRUST_HMAC_KEY'])+'\n',encoding='utf-8')
    path.chmod(0o600)
    print('Created .env. Keep it private. Analyst and Pulse use different keys from this file.')
print('Start: python -m uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8000 --no-access-log')
