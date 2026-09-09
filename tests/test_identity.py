"""B01 regressions: named identity, second factor, role capabilities, tenant isolation, audit, recovery."""
import sqlite3
from contextlib import closing
import time
import uuid

import pytest

from app.accounts import Directory, MAX_FAILED_ATTEMPTS
from app.engine import analyze
from app.identity import (hash_password, verify_password, totp_at, totp_now,
                          verify_totp, new_totp_secret, ROLE_CAPABILITIES)
from app.storage import Store, DEFAULT_ORG_ID
from conftest import PASSWORD

# RFC 6238 appendix B, SHA-1, seed "12345678901234567890" base32-encoded.
RFC_SECRET = 'GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ'


def report_into(store, org_id, url='https://shared.example'):
    scan = analyze('url', url, 'test-secret')
    return store.report(scan, {'scan_id': uuid.uuid4().hex, 'consent_version': '2026-09-09.v1',
                               'category': 'other', 'channel': 'web'}, org_id)


# ---------- primitives ----------

def test_password_hash_is_salted_and_verifiable():
    a, b = hash_password('same-password-twice'), hash_password('same-password-twice')
    assert a != b, 'identical passwords must not produce identical stored values'
    assert verify_password('same-password-twice', a)
    assert not verify_password('wrong-password', a)
    assert not verify_password('x', 'not-a-valid-stored-format')


@pytest.mark.parametrize('unix_time,expected', [(59, '287082'), (1111111109, '081804'), (1234567890, '005924')])
def test_totp_matches_rfc6238_vectors(unix_time, expected):
    assert totp_at(RFC_SECRET, unix_time // 30) == expected


def test_totp_accepts_drift_but_rejects_stale_and_malformed():
    secret = new_totp_secret()
    now = 1_700_000_000
    assert verify_totp(secret, totp_now(secret, now), now)
    assert verify_totp(secret, totp_now(secret, now - 30), now), 'one step of drift is tolerated'
    assert not verify_totp(secret, totp_now(secret, now - 300), now), 'a stale code must fail'
    for bad in ('', '12345', 'abcdef', '1234567', None):
        assert not verify_totp(secret, bad, now)


def test_roles_have_distinct_capabilities():
    assert 'pulse.read' not in ROLE_CAPABILITIES['analyst']
    assert 'reports.read' not in ROLE_CAPABILITIES['pulse']
    assert 'staff.manage' not in ROLE_CAPABILITIES['analyst']


# ---------- session contract ----------

def test_password_alone_grants_no_capability(client, make_staff):
    make_staff(email='half@pilot.test')
    token = client.post('/api/auth/login', json={'email': 'half@pilot.test', 'password': PASSWORD}).json()['session']
    header = {'Authorization': 'Bearer ' + token}
    assert client.get('/api/auth/me', headers=header).json()['mfa_satisfied'] is False
    # The session exists, so this must be 403 (authenticated, not yet authorized), never 200.
    assert client.get('/api/analyst/reports', headers=header).status_code == 403


def test_unknown_email_and_wrong_password_are_indistinguishable(client, make_staff):
    make_staff(email='real@pilot.test')
    missing = client.post('/api/auth/login', json={'email': 'nobody@pilot.test', 'password': PASSWORD})
    wrong = client.post('/api/auth/login', json={'email': 'real@pilot.test', 'password': 'not-the-password'})
    assert missing.status_code == wrong.status_code == 401
    assert missing.json()['detail'] == wrong.json()['detail']


def test_lockout_after_repeated_failures(client, make_staff):
    make_staff(email='target@pilot.test')
    for _ in range(MAX_FAILED_ATTEMPTS):
        client.post('/api/auth/login', json={'email': 'target@pilot.test', 'password': 'wrong'})
    blocked = client.post('/api/auth/login', json={'email': 'target@pilot.test', 'password': PASSWORD})
    assert blocked.status_code == 429, 'the correct password must not bypass an active lockout'
    assert 'Retry-After' in blocked.headers


def test_logout_revokes_the_session(client, sign_in):
    header = {'Authorization': 'Bearer ' + sign_in()}
    assert client.get('/api/analyst/reports', headers=header).status_code == 200
    assert client.post('/api/auth/logout', headers=header).status_code == 204
    assert client.get('/api/analyst/reports', headers=header).status_code == 401


def test_expired_session_is_rejected(client, sign_in, settings):
    header = {'Authorization': 'Bearer ' + sign_in()}
    with closing(sqlite3.connect(settings.database)) as c, c:
        c.execute('UPDATE sessions SET expires_at=?', (int(time.time()) - 1,))
    assert client.get('/api/analyst/reports', headers=header).status_code == 401


def test_disabling_an_account_ends_its_access(client, sign_in, directory, settings):
    header = {'Authorization': 'Bearer ' + sign_in(email='temp@pilot.test')}
    staff_id = client.get('/api/auth/me', headers=header).status_code and \
        next(s['id'] for s in directory.staff_list(DEFAULT_ORG_ID) if s['email'] == 'temp@pilot.test')
    assert directory.set_disabled(staff_id, DEFAULT_ORG_ID, True)
    assert client.get('/api/analyst/reports', headers=header).status_code == 401
    assert client.post('/api/auth/login', json={'email': 'temp@pilot.test', 'password': PASSWORD}).status_code == 401


def test_session_token_is_not_stored_in_the_clear(client, sign_in, settings):
    token = sign_in()
    with closing(sqlite3.connect(settings.database)) as c, c:
        dump = '\n'.join(c.iterdump())
    assert token not in dump
    assert PASSWORD not in dump


# ---------- tenant isolation ----------

def test_reports_and_reviews_are_scoped_to_one_organization(client, app, directory, auth_header):
    store = app.state.store
    other = directory.create_org('Second organization')
    mine = report_into(store, DEFAULT_ORG_ID, 'https://mine.example')
    theirs = report_into(store, other, 'https://theirs.example')

    header = auth_header(email='inside@pilot.test', role='admin')
    listed = client.get('/api/analyst/reports', headers=header).json()['reports']
    ids = {r['id'] for r in listed}
    assert mine['report_id'] in ids
    assert theirs['report_id'] not in ids, 'another organization\'s report must not be listed'

    # Reviewing across the boundary must fail as "not found", not succeed.
    denied = client.patch('/api/analyst/reports/' + theirs['report_id'], headers=header,
                          json={'status': 'accepted', 'reason': 'relevant_evidence'})
    assert denied.status_code == 404
    assert store.reports(other)[0]['status'] == 'pending', 'the foreign report must be untouched'


def test_graph_and_pulse_do_not_leak_across_organizations(app, directory):
    store = app.state.store
    other = directory.create_org('Third organization')
    receipt = report_into(store, other, 'https://elsewhere.example')
    store.review(receipt['report_id'], 'accepted', 'relevant_evidence', other)
    assert store.graph(other)['nodes'], 'sanity: the owning organization can see it'
    assert store.graph(DEFAULT_ORG_ID)['nodes'] == []
    assert store.pulse(1, DEFAULT_ORG_ID)['reviewed_reports'] == 0


def test_staff_management_requires_admin_and_stays_in_organization(client, auth_header, directory):
    other = directory.create_org('Fourth organization')
    outsider = directory.create_staff(other, 'out@other.test', 'Outsider', PASSWORD, 'analyst')
    analyst = auth_header(email='plain@pilot.test', role='analyst')
    admin = auth_header(email='boss@pilot.test', role='admin')

    assert client.get('/api/analyst/staff', headers=analyst).status_code == 403
    listed = client.get('/api/analyst/staff', headers=admin).json()['staff']
    assert all(person['email'] != 'out@other.test' for person in listed)
    denied = client.patch('/api/analyst/staff/' + outsider['staff_id'], headers=admin, json={'disabled': True})
    assert denied.status_code == 404
    assert not directory.staff_list(other)[0]['disabled']


# ---------- audit ----------

def test_review_is_attributed_to_a_named_actor(client, app, auth_header):
    store = app.state.store
    receipt = report_into(store, DEFAULT_ORG_ID)
    header = auth_header(email='reviewer@pilot.test', role='admin')
    client.patch('/api/analyst/reports/' + receipt['report_id'], headers=header,
                 json={'status': 'accepted', 'reason': 'relevant_evidence'})
    events = client.get('/api/analyst/audit', headers=header).json()['events']
    accepted = [e for e in events if e['event'] == 'report.accepted']
    assert accepted and accepted[0]['actor_email'] == 'reviewer@pilot.test'
    assert any(e['event'] == 'auth.mfa_ok' for e in events)


def test_audit_trail_is_scoped_to_the_callers_organization(client, app, directory, auth_header):
    other = directory.create_org('Fifth organization')
    app.state.store.audit('report.created', org_id=other, reason='foreign-event')
    events = client.get('/api/analyst/audit', headers=auth_header(role='admin')).json()['events']
    assert all(e['reason'] != 'foreign-event' for e in events)


def test_failed_sign_in_is_recorded(client, app, make_staff, auth_header):
    make_staff(email='watched@pilot.test')
    client.post('/api/auth/login', json={'email': 'watched@pilot.test', 'password': 'wrong'})
    events = client.get('/api/analyst/audit', headers=auth_header(role='admin')).json()['events']
    assert any(e['event'] == 'auth.failed' and e['reason'] == 'watched@pilot.test' for e in events)


# ---------- retention and recovery ----------

def test_purge_removes_expired_sessions(app, sign_in, settings):
    sign_in()
    with closing(sqlite3.connect(settings.database)) as c, c:
        c.execute('UPDATE sessions SET expires_at=?', (int(time.time()) - 1,))
    assert app.state.store.purge()['sessions'] == 1


def test_backup_verifies_and_restores(tmp_path):
    store = Store(str(tmp_path / 'live.db'))
    directory = Directory(store)
    directory.create_staff(DEFAULT_ORG_ID, 'keep@pilot.test', 'Kept', PASSWORD, 'analyst')
    receipt = report_into(store, DEFAULT_ORG_ID)
    store.review(receipt['report_id'], 'accepted', 'relevant_evidence', DEFAULT_ORG_ID)

    result = store.backup(str(tmp_path / 'copy.db'))
    assert result['verified'] and result['rows']['reports'] == 1 and result['rows']['staff'] == 1

    restored = Store(str(tmp_path / 'copy.db'))
    assert len(restored.reports(DEFAULT_ORG_ID)) == 1
    assert restored.graph(DEFAULT_ORG_ID)['nodes'], 'reviewed associations must survive a restore'
    assert Directory(restored).staff_list(DEFAULT_ORG_ID)[0]['email'] == 'keep@pilot.test'
