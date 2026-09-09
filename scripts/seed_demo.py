"""Seed a labelled local fixture. Never present these rows as real usage or actual scams."""
import sys
import uuid
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.config import Settings
from app.engine import analyze
from app.storage import Store, DEFAULT_ORG_ID
s=Settings.from_env();store=Store(s.database,s.report_ttl_days)
if store.reports(DEFAULT_ORG_ID):
    raise SystemExit('Refusing to append demo rows to a nonempty database. Use a separate clean local database.')
for i in range(6):
    domain='reward-check.test' if i<3 else 'parcel-fee.test'
    result=analyze('message',f'Synthetic demonstration. Send your OTP at https://{domain} and contact @helpdesk_demo.',s.hmac_key)
    receipt=store.report(result,{'scan_id':uuid.uuid4().hex,'consent_version':'2026-09-09.v1','category':'investment','channel':'telegram'},DEFAULT_ORG_ID)
    store.review(receipt['report_id'],'accepted','relevant_evidence',DEFAULT_ORG_ID)
print('Created 6 reviewed SYNTHETIC reports. Select the demo dataset in Trust Pulse. No real users, victims or losses are represented.')
