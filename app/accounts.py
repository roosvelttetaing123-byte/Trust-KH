"""Organization, staff and session directory.

Backed by the same SQLite database as `app/storage.py`, which owns the schema.
Roles and capabilities live in `app/identity.py`; this module only persists them
and enforces the account lifecycle (lockout, session expiry, MFA completion).
"""
import secrets
import time
import uuid

from .identity import (Principal, hash_password, new_session_token, new_totp_secret,
                       provisioning_uri, ROLES, token_fingerprint, verify_password, verify_totp)
from .storage import SESSION_TTL_SECONDS

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_SECONDS = 900
# Comparing against a throwaway hash keeps the "unknown email" path as slow as the
# "wrong password" path, so responses do not disclose which accounts exist.
_DUMMY_HASH = hash_password('trust-kh-timing-equaliser')


class Directory:
    def __init__(self, store):
        self.store = store

    # ---------- organizations ----------

    def create_org(self, name: str, org_id: str | None = None) -> str:
        org_id = org_id or 'org_' + uuid.uuid4().hex[:12]
        with self.store.connect() as c:
            c.execute('INSERT INTO organizations VALUES (?,?,?)', (org_id, name, int(time.time())))
        return org_id

    def organizations(self):
        with self.store.connect() as c:
            return [dict(r) for r in c.execute('SELECT id,name,created_at FROM organizations ORDER BY name')]

    # ---------- staff ----------

    def create_staff(self, org_id: str, email: str, display_name: str, password: str, role: str) -> dict:
        if role not in ROLES:
            raise ValueError(f'Unknown role. Choose one of: {", ".join(sorted(ROLES))}.')
        if len(password) < 12:
            raise ValueError('Use a password of at least 12 characters.')
        email = email.strip().lower()
        secret = new_totp_secret()
        staff_id = 'stf_' + uuid.uuid4().hex[:12]
        with self.store.connect() as c:
            if not c.execute('SELECT 1 FROM organizations WHERE id=?', (org_id,)).fetchone():
                raise ValueError(f'Organization {org_id} does not exist.')
            if c.execute('SELECT 1 FROM staff WHERE email=?', (email,)).fetchone():
                raise ValueError('That email already has an account.')
            c.execute('''INSERT INTO staff(id,org_id,email,display_name,password_hash,totp_secret,role,created_at)
                         VALUES (?,?,?,?,?,?,?,?)''',
                      (staff_id, org_id, email, display_name, hash_password(password), secret, role,
                       int(time.time())))
            self.store._audit(c, 'staff.created', reason=f'{email} as {role}', org_id=org_id)
        # The secret is returned once, at enrolment; it is never exposed by an API route.
        return {'staff_id': staff_id, 'org_id': org_id, 'email': email, 'role': role,
                'totp_secret': secret, 'provisioning_uri': provisioning_uri(secret, email)}

    def staff_list(self, org_id: str):
        with self.store.connect() as c:
            rows = c.execute('''SELECT id,email,display_name,role,disabled,created_at,locked_until
                                FROM staff WHERE org_id=? ORDER BY created_at''', (org_id,)).fetchall()
        return [{**dict(r), 'disabled': bool(r['disabled'])} for r in rows]

    def set_disabled(self, staff_id: str, org_id: str, disabled: bool, actor=None) -> bool:
        with self.store.connect() as c:
            changed = c.execute('UPDATE staff SET disabled=? WHERE id=? AND org_id=?',
                                (int(disabled), staff_id, org_id)).rowcount
            if changed:
                c.execute('DELETE FROM sessions WHERE staff_id=?', (staff_id,))
                self.store._audit(c, 'staff.disabled' if disabled else 'staff.enabled',
                                  reason=staff_id, actor=actor, org_id=org_id)
        return bool(changed)

    # ---------- authentication ----------

    def authenticate(self, email: str, password: str) -> dict:
        """Return {'session': token} on success, else {'error': reason}. Never says which field was wrong."""
        email = (email or '').strip().lower()
        now = int(time.time())
        with self.store.connect() as c:
            row = c.execute('SELECT * FROM staff WHERE email=?', (email,)).fetchone()
            if row is None:
                verify_password(password, _DUMMY_HASH)
                return {'error': 'invalid_credentials'}
            if row['disabled']:
                verify_password(password, _DUMMY_HASH)
                return {'error': 'invalid_credentials'}
            if row['locked_until'] > now:
                return {'error': 'locked', 'retry_after': row['locked_until'] - now}
            if not verify_password(password, row['password_hash']):
                attempts = row['failed_attempts'] + 1
                locked = now + LOCKOUT_SECONDS if attempts >= MAX_FAILED_ATTEMPTS else 0
                c.execute('UPDATE staff SET failed_attempts=?,locked_until=? WHERE id=?',
                          (attempts, locked, row['id']))
                self.store._audit(c, 'auth.failed', reason=email, org_id=row['org_id'])
                return {'error': 'locked', 'retry_after': LOCKOUT_SECONDS} if locked else {'error': 'invalid_credentials'}
            c.execute('UPDATE staff SET failed_attempts=0,locked_until=0 WHERE id=?', (row['id'],))
            token = new_session_token()
            c.execute('''INSERT INTO sessions(id,staff_id,token_hash,created_at,expires_at,mfa_satisfied)
                         VALUES (?,?,?,?,?,0)''',
                      ('ses_' + uuid.uuid4().hex[:12], row['id'], token_fingerprint(token), now,
                       now + SESSION_TTL_SECONDS))
            self.store._audit(c, 'auth.password_ok', reason=email, org_id=row['org_id'])
        # The session exists but carries no capabilities until the second factor succeeds.
        return {'session': token, 'mfa_required': True, 'expires_in': SESSION_TTL_SECONDS}

    def submit_mfa(self, token: str, code: str) -> bool:
        now = int(time.time())
        with self.store.connect() as c:
            row = c.execute('''SELECT s.id AS sid, s.expires_at, f.totp_secret, f.email, f.org_id, f.disabled
                               FROM sessions s JOIN staff f ON f.id=s.staff_id
                               WHERE s.token_hash=?''', (token_fingerprint(token or ''),)).fetchone()
            if not row or row['expires_at'] <= now or row['disabled']:
                return False
            if not verify_totp(row['totp_secret'], code):
                self.store._audit(c, 'auth.mfa_failed', reason=row['email'], org_id=row['org_id'])
                return False
            c.execute('UPDATE sessions SET mfa_satisfied=1 WHERE id=?', (row['sid'],))
            self.store._audit(c, 'auth.mfa_ok', reason=row['email'], org_id=row['org_id'])
        return True

    def principal(self, token: str) -> Principal | None:
        if not token:
            return None
        now = int(time.time())
        with self.store.connect() as c:
            row = c.execute('''SELECT s.mfa_satisfied, s.expires_at, f.id, f.org_id, f.email,
                                      f.display_name, f.role, f.disabled
                               FROM sessions s JOIN staff f ON f.id=s.staff_id
                               WHERE s.token_hash=?''', (token_fingerprint(token),)).fetchone()
        if not row or row['expires_at'] <= now or row['disabled']:
            return None
        return Principal(staff_id=row['id'], org_id=row['org_id'], email=row['email'],
                         display_name=row['display_name'], role=row['role'],
                         mfa_satisfied=bool(row['mfa_satisfied']))

    def end_session(self, token: str) -> bool:
        with self.store.connect() as c:
            row = c.execute('''SELECT s.id AS sid, f.email, f.org_id FROM sessions s
                               JOIN staff f ON f.id=s.staff_id WHERE s.token_hash=?''',
                            (token_fingerprint(token or ''),)).fetchone()
            if not row:
                return False
            c.execute('DELETE FROM sessions WHERE id=?', (row['sid'],))
            self.store._audit(c, 'auth.logout', reason=row['email'], org_id=row['org_id'])
        return True
