"""SQLite local adapter. Reports are minimized and require separate consent.
No message body, screenshot bytes, OTPs, full telephone numbers, or QR accounts are stored.
"""
from collections import Counter
from itertools import combinations
from pathlib import Path
import hashlib
import json
import secrets
import sqlite3
import time
import uuid

class Store:
    def __init__(self, path: str, ttl_days: int = 30):
        self.path, self.ttl_days = path, ttl_days
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as c:
            c.executescript('''
                CREATE TABLE IF NOT EXISTS reports (
                  id TEXT PRIMARY KEY, scan_id TEXT UNIQUE NOT NULL,
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
                CREATE INDEX IF NOT EXISTS observation_key ON observations(indicator_key);
                CREATE TABLE IF NOT EXISTS audit_events (
                  id INTEGER PRIMARY KEY, timestamp INTEGER NOT NULL,
                  event TEXT NOT NULL, report_id TEXT, reason TEXT
                );
                PRAGMA journal_mode=WAL;
            ''')
        try:
            Path(path).chmod(0o600)
        except OSError:
            pass
        self.purge()

    def connect(self):
        c = sqlite3.connect(self.path, timeout=5)
        c.row_factory = sqlite3.Row
        c.execute('PRAGMA foreign_keys=ON')
        return c

    def purge(self):
        now = int(time.time())
        with self.connect() as c:
            c.execute('DELETE FROM reports WHERE expires_at <= ?', (now,))
            c.execute('DELETE FROM audit_events WHERE timestamp < ?', (now-90*86400,))

    def report(self, scan: dict, request: dict) -> dict:
        self.purge()
        now, report_id, token = int(time.time()), uuid.uuid4().hex, secrets.token_urlsafe(32)
        with self.connect() as c:
            try:
                c.execute('''INSERT INTO reports
                  (id,scan_id,delete_hash,created_at,expires_at,consent_version,category,channel,
                   verdict,is_demo,rule_version,signal_codes)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?)''',
                  (report_id,request['scan_id'],hashlib.sha256(token.encode()).hexdigest(),now,
                   now+self.ttl_days*86400,request['consent_version'],request['category'],request['channel'],
                   scan['verdict'],int(scan['is_demo']),scan['rule_version'],
                   json.dumps([s['rule_id'] for s in scan['signals']])))
            except sqlite3.IntegrityError as exc:
                raise ValueError('A report already exists for this check.') from exc
            for item in scan['indicators']:
                c.execute('INSERT INTO observations VALUES (?,?,?,?)',
                          (report_id,item['kind'],item['_key'],item['display']))
            c.execute('INSERT INTO audit_events(timestamp,event,report_id) VALUES (?,?,?)',
                      (now,'report.created',report_id))
        return {'report_id':report_id,'deletion_token':token,'status':'pending',
                'expires_at':now+self.ttl_days*86400,
                'notice':'This is not an official police complaint. Save this receipt to withdraw your report.'}

    def delete(self, report_id: str, token: str) -> bool:
        digest = hashlib.sha256(token.encode()).hexdigest()
        with self.connect() as c:
            row = c.execute('SELECT delete_hash FROM reports WHERE id=?',(report_id,)).fetchone()
            if not row or not secrets.compare_digest(row['delete_hash'],digest):
                return False
            c.execute('DELETE FROM reports WHERE id=?',(report_id,))
            c.execute('INSERT INTO audit_events(timestamp,event,report_id) VALUES (?,?,?)',
                      (int(time.time()),'report.deleted',report_id))
        return True

    def reports(self):
        self.purge()
        with self.connect() as c:
            rows = c.execute('''SELECT id,created_at,expires_at,category,channel,verdict,
                          is_demo,status,rule_version,signal_codes FROM reports
                          ORDER BY created_at DESC LIMIT 100''').fetchall()
            items=[]
            for row in rows:
                obj=dict(row)
                obj['is_demo']=bool(obj['is_demo'])
                obj['signal_codes']=json.loads(obj['signal_codes'])
                obj['indicators']=[dict(x) for x in c.execute(
                    'SELECT kind,display FROM observations WHERE report_id=?',(row['id'],)).fetchall()]
                items.append(obj)
        return items

    def review(self, report_id, status, reason):
        self.purge()
        with self.connect() as c:
            changed=c.execute('UPDATE reports SET status=? WHERE id=?',(status,report_id)).rowcount
            if changed:
                c.execute('INSERT INTO audit_events(timestamp,event,report_id,reason) VALUES (?,?,?,?)',
                          (int(time.time()),'report.'+status,report_id,reason))
            return bool(changed)

    def graph(self):
        self.purge()
        nodes, edges, observations = {}, Counter(), {}
        with self.connect() as c:
            # Bounded local demo graph. Reviews establish relevance, NOT criminal attribution.
            rows=c.execute('''SELECT o.*,r.is_demo FROM observations o JOIN reports r ON r.id=o.report_id
                              WHERE r.status='accepted' ORDER BY r.created_at DESC LIMIT 500''').fetchall()
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

    def pulse(self, minimum: int, demo=False):
        self.purge()
        with self.connect() as c:
            rows=c.execute('''SELECT category,COUNT(*) AS n FROM reports WHERE status='accepted'
                              AND is_demo=? GROUP BY category''',(int(demo),)).fetchall()
        visible=[{'category':r['category'],'reports':r['n']} for r in rows if r['n']>=minimum]
        suppressed=any(r['n']<minimum for r in rows)
        return {'dataset':'synthetic_demo' if demo else 'consented_reports',
                'categories':visible,'small_cells_suppressed':suppressed,
                # Complementary suppression: don't reveal a total that exposes hidden cells.
                'reviewed_reports':None if suppressed else sum(r['n'] for r in rows),
                'minimum_cell_size':minimum,
                'notice':'Reviewed submitted reports only; not national scam prevalence or unique victims. Small-cell suppression is not an anonymity guarantee. No names, messages, raw indicators or locations are exposed.'}
