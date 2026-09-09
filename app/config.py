"""Local configuration. Public deployment deliberately requires a separate hardening pass."""
from dataclasses import dataclass
from pathlib import Path
import os

ROOT = Path(__file__).resolve().parents[1]

@dataclass(frozen=True)
class Settings:
    database: str
    hmac_key: str
    scan_ttl_seconds: int = 900
    report_ttl_days: int = 30
    rate_limit: int = 30
    max_scans: int = 1000
    minimum_cohort: int = 5

    @classmethod
    def from_env(cls):
        # Small .env reader: literal KEY=VALUE only; existing environment wins.
        file = ROOT / '.env'
        if file.exists():
            for line in file.read_text(encoding='utf-8').splitlines():
                if line.strip() and not line.lstrip().startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ.setdefault(key.strip(), value.strip())
        env = os.getenv('TRUST_ENV', 'local')
        if env not in {'local', 'test'}:
            raise RuntimeError('This starter only supports local/test. Complete docs/RELEASE_GATES.md before creating a production configuration.')
        # Staff access is authenticated per named account (app/accounts.py), so the only
        # remaining server secret is the indicator-fingerprinting key.
        hmac_key = os.getenv('TRUST_HMAC_KEY', '')
        if len(hmac_key) < 32:
            raise RuntimeError('Generate the local secret and first admin: python scripts/init_local.py')
        return cls(os.getenv('TRUST_DB', str(ROOT / 'data' / 'trust.db')), hmac_key)
