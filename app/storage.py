"""SQLite local adapter. Reports are minimized and require separate consent.
No message body, screenshot bytes, OTPs, full telephone numbers, or QR accounts are stored.

This module owns the whole schema, including the identity tables read by
`app/accounts.py`, so there is a single portable definition to migrate to
PostgreSQL when a deployment target exists (B01b, not yet done).
"""
from collections import Counter
from contextlib import closing, contextmanager
from itertools import combinations
from pathlib import Path
import hashlib
import json
import secrets
import sqlite3
import time
import uuid

DEFAULT_ORG_ID = 'org_pilot'
SESSION_TTL_SECONDS = 12 * 3600
AUDIT_TTL_DAYS = 365

# Tables first, then migrations, then indexes: an index may reference a column that
# `CREATE TABLE IF NOT EXISTS` skipped adding to an already-existing table.
SCHEMA_TABLES = '''
CREATE TABLE IF NOT EXISTS organizations (
  id TEXT PRIMARY KEY, name TEXT NOT NULL, created_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS staff (
  id TEXT PRIMARY KEY,
  org_id TEXT NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  email TEXT NOT NULL, display_name TEXT NOT NULL,
  password_hash TEXT NOT NULL, totp_secret TEXT NOT NULL,
  role TEXT NOT NULL, disabled INTEGER NOT NULL DEFAULT 0,
  created_at INTEGER NOT NULL,
  failed_attempts INTEGER NOT NULL DEFAULT 0, locked_until INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS sessions (
  id TEXT PRIMARY KEY,
  staff_id TEXT NOT NULL REFERENCES staff(id) ON DELETE CASCADE,
  token_hash TEXT NOT NULL UNIQUE, created_at INTEGER NOT NULL,
  expires_at INTEGER NOT NULL, mfa_satisfied INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS reports (
  id TEXT PRIMARY KEY, scan_id TEXT UNIQUE NOT NULL,
  org_id TEXT NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  delete_hash TEXT NOT NULL, created_at INTEGER NOT NULL,
  expires_at INTEGER NOT NULL, consent_version TEXT NOT NULL,
  category TEXT NOT NULL, channel TEXT NOT NULL, verdict TEXT NOT NULL,
  is_demo INTEGER NOT NULL, status TEXT NOT NULL DEFAULT 'pending',
  rule_version TEXT NOT NULL, signal_codes TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS observations (
  report_id TEXT NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
  kind TEXT NOT NULL, indicator_key TEXT NOT NULL, display TEXT NOT NULL,
  PRIMARY KEY(report_id,kind,indicator_key)
);
CREATE TABLE IF NOT EXISTS audit_events (
  id INTEGER PRIMARY KEY, timestamp INTEGER NOT NULL,
  event TEXT NOT NULL, report_id TEXT, reason TEXT,
  actor_id TEXT, actor_email TEXT, org_id TEXT
);
'''

SCHEMA_INDEXES = '''
CREATE UNIQUE INDEX IF NOT EXISTS staff_email ON staff(email);
CREATE INDEX IF NOT EXISTS report_org ON reports(org_id);
CREATE INDEX IF NOT EXISTS observation_key ON observations(indicator_key);
CREATE INDEX IF NOT EXISTS audit_org ON audit_events(org_id,timestamp);
'''


class Store:
    def __init__(self, path: str, ttl_days: int = 30):
        self.path, self.ttl_days = path, ttl_days
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as c:
            c.executescript(SCHEMA_TABLES)
            c.execute('PRAGMA journal_mode=WAL')
            self._migrate(c)
            c.executescript(SCHEMA_INDEXES)
            c.execute('INSERT OR IGNORE INTO organizations VALUES (?,?,?)',
                      (DEFAULT_ORG_ID, 'Pilot organization', int(time.time())))
        try:
            Path(path).chmod(0o600)
        except OSError:
            pass
        self.purge()

    @staticmethod
    def _migrate(c):
        """Add columns introduced after a database was first created."""
        for table, column, ddl in (
            ('reports', 'org_id', f"ALTER TABLE reports ADD COLUMN org_id TEXT NOT NULL DEFAULT '{DEFAULT_ORG_ID}'"),
            ('audit_events', 'actor_id', 'ALTER TABLE audit_events ADD COLUMN actor_id TEXT'),
            ('audit_events', 'actor_email', 'ALTER TABLE audit_events ADD COLUMN actor_email TEXT'),
            ('audit_events', 'org_id', 'ALTER TABLE audit_events ADD COLUMN org_id TEXT'),
        ):
            existing = {r['name'] for r in c.execute(f'PRAGMA table_info({table})').fetchall()}
            if column not in existing:
                c.execute(ddl)

    @contextmanager
    def connect(self):
        """Commit-or-rollback AND close.

        `with sqlite3.connect(...)` only ends the transaction; it leaves the handle
        open, which leaks file descriptors and keeps the file locked on Windows.
        """
        c = sqlite3.connect(self.path, timeout=5)
        c.row_factory = sqlite3.Row
        c.execute('PRAGMA foreign_keys=ON')
        try:
            with c:
                yield c
        finally:
            c.close()

    def purge(self):
        """Retention job: expire reports, stale sessions and old audit history."""
        now = int(time.time())
        with self.connect() as c:
            reports = c.execute('DELETE FROM reports WHERE expires_at <= ?', (now,)).rowcount
            sessions = c.execute('DELETE FROM sessions WHERE expires_at <= ?', (now,)).rowcount
            audit = c.execute('DELETE FROM audit_events WHERE timestamp < ?',
                              (now - AUDIT_TTL_DAYS * 86400,)).rowcount
        return {'reports': max(reports, 0), 'sessions': max(sessions, 0), 'audit_events': max(audit, 0)}

    def audit(self, event, *, report_id=None, reason=None, actor=None, org_id=None):
        with self.connect() as c:
            self._audit(c, event, report_id=report_id, reason=reason, actor=actor, org_id=org_id)

    @staticmethod
    def _audit(c, event, *, report_id=None, reason=None, actor=None, org_id=None):
        c.execute('''INSERT INTO audit_events(timestamp,event,report_id,reason,actor_id,actor_email,org_id)
                     VALUES (?,?,?,?,?,?,?)''',
                  (int(time.time()), event, report_id, reason,
                   getattr(actor, 'staff_id', None), getattr(actor, 'email', None),
                   org_id or getattr(actor, 'org_id', None)))

    def audit_trail(self, org_id: str, limit: int = 100):
        """Scoped to one organization: an audit log is itself sensitive evidence."""
        with self.connect() as c:
            rows = c.execute('''SELECT timestamp,event,report_id,reason,actor_email FROM audit_events
                                WHERE org_id=? ORDER BY timestamp DESC, id DESC LIMIT ?''',
                             (org_id, min(int(limit), 500))).fetchall()
        return [dict(r) for r in rows]

    def report(self, scan: dict, request: dict, org_id: str = DEFAULT_ORG_ID) -> dict:
        self.purge()
        now, report_id, token = int(time.time()), uuid.uuid4().hex, secrets.token_urlsafe(32)
        with self.connect() as c:
            try:
                c.execute('''INSERT INTO reports
                  (id,scan_id,org_id,delete_hash,created_at,expires_at,consent_version,category,channel,
                   verdict,is_demo,rule_version,signal_codes)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                  (report_id,request['scan_id'],org_id,hashlib.sha256(token.encode()).hexdigest(),now,
                   now+self.ttl_days*86400,request['consent_version'],request['category'],request['channel'],
                   scan['verdict'],int(scan['is_demo']),scan['rule_version'],
                   json.dumps([s['rule_id'] for s in scan['signals']])))
            except sqlite3.IntegrityError as exc:
                raise ValueError('A report already exists for this check.') from exc
            for item in scan['indicators']:
                c.execute('INSERT INTO observations VALUES (?,?,?,?)',
                          (report_id,item['kind'],item['_key'],item['display']))
            self._audit(c,'report.created',report_id=report_id,org_id=org_id)
        return {'report_id':report_id,'deletion_token':token,'status':'pending',
                'expires_at':now+self.ttl_days*86400,
                'notice':'This is not an official police complaint. Save this receipt to withdraw your report.'}

    def delete(self, report_id: str, token: str) -> bool:
        """Citizen withdrawal. Authorized by the receipt token, not by staff role."""
        digest = hashlib.sha256(token.encode()).hexdigest()
        with self.connect() as c:
            row = c.execute('SELECT delete_hash,org_id FROM reports WHERE id=?',(report_id,)).fetchone()
            if not row or not secrets.compare_digest(row['delete_hash'],digest):
                return False
            c.execute('DELETE FROM reports WHERE id=?',(report_id,))
            self._audit(c,'report.deleted',report_id=report_id,org_id=row['org_id'])
        return True

    def reports(self, org_id: str):
        self.purge()
        with self.connect() as c:
            rows = c.execute('''SELECT id,created_at,expires_at,category,channel,verdict,
                          is_demo,status,rule_version,signal_codes FROM reports
                          WHERE org_id=? ORDER BY created_at DESC LIMIT 100''',(org_id,)).fetchall()
            items=[]
            for row in rows:
                obj=dict(row)
                obj['is_demo']=bool(obj['is_demo'])
                obj['signal_codes']=json.loads(obj['signal_codes'])
                obj['indicators']=[dict(x) for x in c.execute(
                    'SELECT kind,display FROM observations WHERE report_id=?',(row['id'],)).fetchall()]
                items.append(obj)
        return items

    def review(self, report_id, status, reason, org_id: str, actor=None):
        self.purge()
        with self.connect() as c:
            # org_id in the predicate is the tenant boundary: another organization's
            # report is not found rather than updated.
            changed=c.execute('UPDATE reports SET status=? WHERE id=? AND org_id=?',
                              (status,report_id,org_id)).rowcount
            if changed:
                self._audit(c,'report.'+status,report_id=report_id,reason=reason,
                            actor=actor,org_id=org_id)
            return bool(changed)

    def graph(self, org_id: str):
        self.purge()
        nodes, edges, observations = {}, Counter(), {}
        with self.connect() as c:
            # Bounded local demo graph. Reviews establish relevance, NOT criminal attribution.
            rows=c.execute('''SELECT o.*,r.is_demo FROM observations o JOIN reports r ON r.id=o.report_id
                              WHERE r.status='accepted' AND r.org_id=?
                              ORDER BY r.created_at DESC LIMIT 500''',(org_id,)).fetchall()
            for row in rows:
                # The same indicator in demo and non-demo rows must not merge.
                key=(bool(row['is_demo']), row['indicator_key'])
                if key not in nodes:
                    # Return opaque graph-local numeric IDs, never HMAC fingerprints.
                    nodes[key]={'id':str(len(nodes)+1),'label':row['display'],'kind':row['kind'],
                                'reports':0,'is_demo':bool(row['is_demo'])}
                nodes[key]['reports']+=1
                observations.setdefault(row['report_id'],set()).add(key)
            for keys in observations.values():
                for a,b in combinations(sorted(keys),2):
                    edges[(a,b)]+=1
        return {'nodes':list(nodes.values()),
                'edges':[{'source':nodes[a]['id'],'target':nodes[b]['id'],'reports':count}
                         for (a,b),count in edges.items()],
                'notice':'Co-occurrence in reviewed reports is an association, not proof of a shared criminal operator. Synthetic records are labelled.'}

    def pulse(self, minimum: int, org_id: str, demo=False):
        self.purge()
        with self.connect() as c:
            rows=c.execute('''SELECT category,COUNT(*) AS n FROM reports WHERE status='accepted'
                              AND is_demo=? AND org_id=? GROUP BY category''',(int(demo),org_id)).fetchall()
        visible=[{'category':r['category'],'reports':r['n']} for r in rows if r['n']>=minimum]
        suppressed=any(r['n']<minimum for r in rows)
        return {'dataset':'synthetic_demo' if demo else 'consented_reports',
                'categories':visible,'small_cells_suppressed':suppressed,
                # Complementary suppression: don't reveal a total that exposes hidden cells.
                'reviewed_reports':None if suppressed else sum(r['n'] for r in rows),
                'minimum_cell_size':minimum,
                'notice':'Reviewed submitted reports for this organization only; not national scam prevalence or unique victims. Cross-organization publication requires a disclosure-review pipeline that is not built. Small-cell suppression is not an anonymity guarantee.'}

    def backup(self, destination: str) -> dict:
        """Consistent online copy via the SQLite backup API, then verify the copy."""
        Path(destination).parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as source, closing(sqlite3.connect(destination)) as target:
            source.backup(target)
        with closing(sqlite3.connect(destination)) as check:
            if check.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                raise RuntimeError('Backup failed its integrity check and must not be relied on.')
            counts = {t: check.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]
                      for t in ('organizations','staff','reports','observations','audit_events')}
        try:
            Path(destination).chmod(0o600)
        except OSError:
            pass
        return {'path': destination, 'verified': True, 'rows': counts}
