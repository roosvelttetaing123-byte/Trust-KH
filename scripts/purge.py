"""Run via a daily scheduler after a production deployment has been hardened."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.config import Settings
from app.storage import Store
s=Settings.from_env()
Store(s.database,s.report_ttl_days).purge()
print('Expired reports/observations and old audit records removed from active local database.')
