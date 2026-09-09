"""Local configuration. Public deployment deliberately requires a separate hardening pass."""
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit
import os

ROOT = Path(__file__).resolve().parents[1]

LOCAL_ORIGINS = ('http://127.0.0.1:8000', 'http://localhost:8000', 'http://testserver')
LOOPBACK_HOSTS = {'localhost', '127.0.0.1', '::1', 'testserver'}


def is_loopback_origin(origin: str) -> bool:
    """Any port on the local machine counts.

    Pinning loopback to one port only breaks running a second local build (the demo
    alongside the dev server) and buys nothing: anything already on this machine can
    bind whichever port it likes.
    """
    try:
        parts = urlsplit(origin)
    except ValueError:
        return False
    return parts.scheme in ('http', 'https') and parts.hostname in LOOPBACK_HOSTS
# 'demo' is a deliberate, documented mode for a hosted synthetic walkthrough (Gate A in
# docs/RELEASE_GATES.md, extended to a public URL). It refuses citizen report intake, so
# no real evidence can be collected. It is NOT Gate C: do not add a 'production' value
# here to get a public intake service.
ALLOWED_ENVS = {'local', 'test', 'demo'}


@dataclass(frozen=True)
class Settings:
    database: str
    hmac_key: str
    scan_ttl_seconds: int = 900
    report_ttl_days: int = 30
    rate_limit: int = 30
    max_scans: int = 1000
    minimum_cohort: int = 5
    demo: bool = False
    allowed_origins: tuple[str, ...] = field(default=LOCAL_ORIGINS)

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
        if env not in ALLOWED_ENVS:
            raise RuntimeError('This project supports local/test/demo only. Complete docs/RELEASE_GATES.md '
                               'before creating a public citizen-intake configuration.')
        # Staff access is authenticated per named account (app/accounts.py), so the only
        # remaining server secret is the indicator-fingerprinting key.
        hmac_key = os.getenv('TRUST_HMAC_KEY', '')
        if len(hmac_key) < 32:
            raise RuntimeError('Generate the local secret and first admin: python scripts/init_local.py')

        demo = env == 'demo'
        origins = tuple(o.strip().rstrip('/') for o in os.getenv('TRUST_ORIGIN', '').split(',') if o.strip())
        if demo and not origins:
            raise RuntimeError('Demo mode needs TRUST_ORIGIN set to the public https origin, '
                               'e.g. TRUST_ORIGIN=https://trust-kh-demo.example')
        if any(not o.startswith('https://') for o in origins):
            raise RuntimeError('TRUST_ORIGIN entries must be https:// origins.')

        # Keep the loopback origins allowed alongside a deployed one so the exact demo
        # build can be exercised locally before it is published. Staff auth is a bearer
        # token rather than a cookie, so this is defence in depth, not the CSRF control.
        return cls(os.getenv('TRUST_DB', str(ROOT / 'data' / 'trust.db')), hmac_key,
                   demo=demo, allowed_origins=tuple(dict.fromkeys(origins + LOCAL_ORIGINS)))
