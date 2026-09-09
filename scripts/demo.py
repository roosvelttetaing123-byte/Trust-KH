"""Run the hosted-demo build locally, so it can be checked before it is published.

Uses the same TRUST_ENV=demo path as the deployment: report intake is refused by the
server and the interface says so. Uses a scratch database, never the pilot one.
"""
import os
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
os.chdir(root)
if not (root / '.env').exists():
    subprocess.run([sys.executable, 'scripts/init_local.py'], check=True)

env = dict(os.environ,
           TRUST_ENV='demo',
           TRUST_ORIGIN=os.getenv('TRUST_ORIGIN', 'https://trust-kh-demo.invalid'),
           TRUST_DB=os.getenv('TRUST_DB', str(root / 'data' / 'demo.db')))
port = os.getenv('PORT', '8010')
print(f'Demo build on http://127.0.0.1:{port} — report intake is refused by the server.')
subprocess.run([sys.executable, '-m', 'uvicorn', 'app.main:create_app', '--factory',
                '--host', '127.0.0.1', '--port', port, '--no-access-log'], check=True, env=env)
