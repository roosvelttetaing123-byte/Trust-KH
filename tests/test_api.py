import io
import json
import sqlite3
from contextlib import closing
import time
from pypdf import PdfReader
import qrcode
from PIL import Image
from app.storage import DEFAULT_ORG_ID


def scan(client,text='Please send your OTP now. Visit https://reward-check.test with @helpdesk_demo.'):
    response=client.post('/api/scans',json={'kind':'message','text':text})
    assert response.status_code==201,response.text
    return response.json()

def auth(token): return {'Authorization':'Bearer '+token}

def report(client,s,category='investment'):
    return client.post('/api/reports',json={'scan_id':s['scan_id'],'consent':True,'consent_version':'2026-09-09.v1','category':category,'channel':'telegram'},headers=auth(s['access_token']))

def test_health_and_frontend(client):
    assert client.get('/api/health').json()['live_reputation'] is False
    response=client.get('/')
    assert response.status_code==200
    assert 'ពិនិត្យមុននឹងជឿ' in response.text
    assert "frame-ancestors 'none'" in response.headers['content-security-policy']

def test_result_requires_secret_capability(client):
    s=scan(client)
    url='/api/scans/'+s['scan_id']
    assert client.get(url).status_code==404
    assert client.get(url,headers=auth('wrong')).status_code==404
    assert client.get(url,headers=auth(s['access_token'])).status_code==200
    assert client.get(url,headers=auth(s['access_token'])).headers['cache-control']=='no-store'

def test_scan_is_transient_and_delete_works(client,app):
    s=scan(client)
    url='/api/scans/'+s['scan_id']
    assert client.delete(url,headers=auth(s['access_token'])).status_code==204
    assert client.get(url,headers=auth(s['access_token'])).status_code==404
    s=scan(client)
    app.state.scans.data[s['scan_id']].expiry=time.time()-1
    assert client.get('/api/scans/'+s['scan_id'],headers=auth(s['access_token'])).status_code==404

def test_report_needs_separate_explicit_consent(client):
    s=scan(client)
    r=client.post('/api/reports',headers=auth(s['access_token']),json={'scan_id':s['scan_id'],'consent':False,'consent_version':'2026-09-09.v1'})
    assert r.status_code==422
    r=client.post('/api/reports',headers=auth(s['access_token']),json={'scan_id':s['scan_id'],'consent':True,'consent_version':'wrong'})
    assert r.status_code==422

def test_report_minimization_and_dedup(client,settings):
    s=scan(client,'Please send your OTP 998877. Go to https://reward-check.test/private-secret?token=abc and call 012345678.')
    response=report(client,s)
    assert response.status_code==201
    assert report(client,s).status_code==409
    with closing(sqlite3.connect(settings.database)) as c, c:
        dump='\n'.join(c.iterdump())
    for value in ['998877','private-secret','token=abc','012345678','Please send your OTP']:
        assert value not in dump
    assert response.json()['deletion_token'] not in dump

def test_delete_report_cascades_observations(client,settings):
    r=report(client,scan(client)).json()
    assert client.delete('/api/reports/'+r['report_id'],headers=auth('wrong')).status_code==404
    assert client.delete('/api/reports/'+r['report_id'],headers=auth(r['deletion_token'])).status_code==204
    with closing(sqlite3.connect(settings.database)) as c, c:
        assert c.execute('SELECT COUNT(*) FROM observations').fetchone()[0]==0
        assert c.execute('SELECT COUNT(*) FROM reports').fetchone()[0]==0

def test_analyst_and_pulse_roles_separated(client,auth_header):
    assert client.get('/api/analyst/reports').status_code==401
    assert client.get('/api/pulse').status_code==401
    analyst=auth_header(email='a@pilot.test',role='analyst')
    viewer=auth_header(email='p@pilot.test',role='pulse')
    # A role boundary, not just an authentication boundary.
    assert client.get('/api/analyst/reports',headers=viewer).status_code==403
    assert client.get('/api/pulse',headers=analyst).status_code==403
    assert client.get('/api/analyst/reports',headers=analyst).status_code==200
    assert client.get('/api/pulse',headers=viewer).status_code==200

def test_pending_reports_do_not_change_risk_or_graph(client,auth_header):
    header=auth_header(role='admin')
    for _ in range(4):
        s=scan(client,'See https://unfamiliar.test with @helpdesk_demo.')
        report(client,s)
    g=client.get('/api/analyst/graph',headers=header).json()
    assert not g['nodes']
    assert scan(client,'See https://unfamiliar.test')['verdict']=='unknown'

def test_review_adds_associations_not_blocklist(client,auth_header):
    header=auth_header(role='admin')
    s=scan(client,'Visit https://ordinary.test and contact @helpdesk_demo.')
    r=report(client,s).json()
    response=client.patch('/api/analyst/reports/'+r['report_id'],headers=header,json={'status':'accepted','reason':'relevant_evidence'})
    assert response.status_code==200
    g=client.get('/api/analyst/graph',headers=header).json()
    assert len(g['nodes'])==2 and len(g['edges'])==1
    assert 'indicator_key' not in json.dumps(g)
    assert scan(client,'Visit https://ordinary.test')['verdict']=='unknown'

def test_pulse_small_cell_and_demo_separation(client,auth_header):
    header=auth_header(role='admin')
    for _ in range(5):
        r=report(client,scan(client)).json()
        client.patch('/api/analyst/reports/'+r['report_id'],headers=header,json={'status':'accepted','reason':'relevant_evidence'})
    production=client.get('/api/pulse',headers=header).json()
    demo=client.get('/api/pulse/demo',headers=header).json()
    assert production['reviewed_reports']==0
    assert demo['reviewed_reports']==5
    r=report(client,scan(client),category='shopping').json()
    client.patch('/api/analyst/reports/'+r['report_id'],headers=header,json={'status':'accepted','reason':'relevant_evidence'})
    demo=client.get('/api/pulse/demo',headers=header).json()
    assert demo['reviewed_reports'] is None
    assert demo['small_cells_suppressed']
    assert len(demo['categories'])==1

def test_export_is_not_official_or_original_evidence(client):
    s=scan(client)
    response=client.get('/api/scans/'+s['scan_id']+'/export?lang=en',headers=auth(s['access_token']))
    assert response.status_code==200
    assert response.headers['content-type']=='application/pdf'
    reader=PdfReader(io.BytesIO(response.content))
    content=' '.join(p.extract_text() for p in reader.pages)
    assert 'not a certificate or an official complaint' in content
    assert s['access_token'] not in content
    assert 'No original messages' in content
    assert not reader.attachments

def test_foreign_origin_blocked(client):
    r=client.post('/api/scans',json={'kind':'message','text':'Hello'},headers={'Origin':'https://unrelated.test'})
    assert r.status_code==403

def test_static_assets_ignore_origin(client):
    """A wrong TRUST_ORIGIN must not disable the app.

    Module scripts and webfonts are fetched in CORS mode and send Origin even
    same-origin. Blocking GET on Origin therefore returned 403 for /app.js while
    /style.css still loaded, so a misconfigured deploy rendered a correct-looking
    page with no working JavaScript at all.
    """
    foreign={'Origin':'https://wrong-origin.test'}
    for path in ('/','/app.js','/i18n.js','/style.css','/fonts/kantumruy-pro-khmer.woff2'):
        assert client.get(path,headers=foreign).status_code==200, f'{path} must load regardless of Origin'
    # Reads stay open; only state-changing requests are origin-checked.
    assert client.get('/api/health',headers=foreign).status_code==200
    assert client.post('/api/scans',json={'kind':'message','text':'Hi'},headers=foreign).status_code==403

def test_validation_does_not_echo_sensitive_input(client):
    r=client.post('/api/scans',json={'kind':'other','text':'MY-SECRET-OTP-112233'})
    assert r.status_code==422
    assert 'MY-SECRET' not in r.text

def test_body_size_capped(client):
    r=client.post('/api/scans',content=b'x'*40000,headers={'Content-Type':'application/json'})
    assert r.status_code==413

def test_decode_real_qr_image_without_network(client):
    image=qrcode.make('https://ordinary-shop.test/catalog')
    buffer=io.BytesIO();image.save(buffer,format='PNG')
    r=client.post('/api/qr/decode',content=buffer.getvalue(),headers={'Content-Type':'image/png'})
    assert r.status_code==200,r.text
    assert r.json()['text']=='https://ordinary-shop.test/catalog'

def test_no_qr_and_invalid_image_have_clear_errors(client):
    buffer=io.BytesIO();Image.new('RGB',(64,64),'white').save(buffer,format='PNG')
    r=client.post('/api/qr/decode',content=buffer.getvalue(),headers={'Content-Type':'image/png'})
    assert r.status_code==422
    assert 'Screenshot text extraction is not implemented' in r.json()['detail']
    assert client.post('/api/qr/decode',content=b'not-an-image',headers={'Content-Type':'image/png'}).status_code==422
    assert client.post('/api/qr/decode',content=b'<svg/>',headers={'Content-Type':'image/svg+xml'}).status_code==415

def test_expired_reports_purged(client,settings,app):
    r=report(client,scan(client)).json()
    with closing(sqlite3.connect(settings.database)) as c, c:
        c.execute('UPDATE reports SET expires_at=0')
    app.state.store.purge()
    assert not app.state.store.reports(DEFAULT_ORG_ID)

def test_openapi_is_available(client):
    document=client.get('/api/openapi.json').json()
    assert '/api/scans' in document['paths']
