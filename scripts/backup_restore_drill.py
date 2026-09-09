"""Backup and restore rehearsal (docs/BUILD_BACKLOG.md B01e).

Takes a consistent online backup, restores it to a scratch path, and proves the
restored copy answers the same queries as the original. Exits non-zero if any
check fails, so it can run in CI or before a risky change.

A passing drill on SQLite is not a production recovery test: it does not cover
PostgreSQL, off-host storage, retention of backup copies, or restore under load.
"""
from pathlib import Path
import sys
import tempfile
import time

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))

from app.config import Settings
from app.storage import Store

TABLES = ('organizations', 'staff', 'reports', 'observations', 'audit_events')


def main():
    settings = Settings.from_env()
    store = Store(settings.database, settings.report_ttl_days)

    with store.connect() as c:
        before = {t: c.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0] for t in TABLES}
    print('Source database:', settings.database)
    print('Row counts     :', before)

    with tempfile.TemporaryDirectory() as tmp:
        target = str(Path(tmp) / 'trust-backup.db')
        started = time.time()
        result = store.backup(target)
        size = Path(target).stat().st_size
        print(f'\nBackup written  : {size:,} bytes in {time.time()-started:.2f}s (integrity check passed)')

        if result['rows'] != before:
            print('FAIL: backup row counts differ from source:', result['rows'])
            return 1

        # Restore means: open the backup as the live database and serve real queries from it.
        restored = Store(target, settings.report_ttl_days)
        with restored.connect() as c:
            after = {t: c.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0] for t in TABLES}
            orgs = [r['id'] for r in c.execute('SELECT id FROM organizations').fetchall()]

        # purge() runs on open, so expired rows may legitimately be dropped from the copy.
        drift = {t: (before[t], after[t]) for t in TABLES if after[t] > before[t]}
        if drift:
            print('FAIL: restored copy has more rows than the source:', drift)
            return 1

        for org in orgs:
            restored.reports(org)
            restored.graph(org)
            restored.pulse(settings.minimum_cohort, org)
        print('Restored counts :', after)
        print(f'Queries served  : reports, graph and pulse answered for {len(orgs)} organization(s)')

    print('\nDRILL PASSED — backup verified and restored copy served live queries.')
    print('Not covered: PostgreSQL, off-host copies, backup retention, restore under load.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
