import io
import json
import sqlite3
import time
import zipfile
import qrcode
from PIL import Image


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
    assert 'Check before you trust' in response.text
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
    with sqlite3.connect(settings.database) as c:
        dump='\n'.join(c.iterdump())
    for value in ['998877','private-secret','token=abc','012345678','Please send your OTP']:
        assert value not in dump
    assert response.json()['deletion_token'] not in dump

def test_delete_report_cascades_observations(client,settings):
    r=report(client,scan(client)).json()
    assert client.delete('/api/reports/'+r['report_id'],headers=auth('wrong')).status_code==404
    assert client.delete('/api/reports/'+r['report_id'],headers=auth(r['deletion_token'])).status_code==204
    with sqlite3.connect(settings.database) as c:
        assert c.execute('SELECT COUNT(*) FROM observations').fetchone()[0]==0
        assert c.execute('SELECT COUNT(*) FROM reports').fetchone()[0]==0

def test_analyst_and_pulse_roles_separated(client,settings):
    assert client.get('/api/analyst/reports').status_code==401
    assert client.get('/api/pulse').status_code==401
    assert client.get('/api/analyst/reports',headers=auth(settings.pulse_key)).status_code==401
    assert client.get('/api/pulse',headers=auth(settings.admin_key)).status_code==401
    assert client.get('/api/pulse',headers=auth(settings.pulse_key)).status_code==200

def test_pending_reports_do_not_change_risk_or_graph(client,settings):
    for _ in range(4):
        s=scan(client,'See https://unfamiliar.test with @helpdesk_demo.')
        report(client,s)
    g=client.get('/api/analyst/graph',headers=auth(settings.admin_key)).json()
    assert not g['nodes']
    assert scan(client,'See https://unfamiliar.test')['verdict']=='unknown'

def test_review_adds_associations_not_blocklist(client,settings):
    s=scan(client,'Visit https://ordinary.test and contact @helpdesk_demo.')
    r=report(client,s).json()
    response=client.patch('/api/analyst/reports/'+r['report_id'],headers=auth(settings.admin_key),json={'status':'accepted','reason':'relevant_evidence'})
    assert response.status_code==200
    g=client.get('/api/analyst/graph',headers=auth(settings.admin_key)).json()
    assert len(g['nodes'])==2 and len(g['edges'])==1
    assert 'indicator_key' not in json.dumps(g)
    assert scan(client,'Visit https://ordinary.test')['verdict']=='unknown'

def test_pulse_small_cell_and_demo_separation(client,settings):
    for _ in range(5):
        r=report(client,scan(client)).json()
        client.patch('/api/analyst/reports/'+r['report_id'],headers=auth(settings.admin_key),json={'status':'accepted','reason':'relevant_evidence'})
    production=client.get('/api/pulse',headers=auth(settings.pulse_key)).json()
    demo=client.get('/api/pulse/demo',headers=auth(settings.pulse_key)).json()
    assert production['reviewed_reports']==0
    assert demo['reviewed_reports']==5
    r=report(client,scan(client),category='shopping').json()
    client.patch('/api/analyst/reports/'+r['report_id'],headers=auth(settings.admin_key),json={'status':'accepted','reason':'relevant_evidence'})
    demo=client.get('/api/pulse/demo',headers=auth(settings.pulse_key)).json()
    assert demo['reviewed_reports'] is None
    assert demo['small_cells_suppressed']
    assert len(demo['categories'])==1

def test_export_is_not_official_or_original_evidence(client):
    s=scan(client)
    response=client.get('/api/scans/'+s['scan_id']+'/export',headers=auth(s['access_token']))
    assert response.status_code==200
    with zipfile.ZipFile(io.BytesIO(response.content)) as z:
        summary=json.loads(z.read('summary.json'))
        all_content=' '.join(z.read(name).decode() for name in z.namelist())
    assert not summary['official_report_submitted']
    assert s['access_token'] not in all_content
    assert '_key' not in all_content
    assert 'original images' in all_content

def test_foreign_origin_blocked(client):
    r=client.post('/api/scans',json={'kind':'message','text':'Hello'},headers={'Origin':'https://unrelated.test'})
    assert r.status_code==403

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
    with sqlite3.connect(settings.database) as c:
        c.execute('UPDATE reports SET expires_at=0')
    app.state.store.purge()
    assert not app.state.store.reports()

def test_openapi_is_available(client):
    document=client.get('/api/openapi.json').json()
    assert '/api/scans' in document['paths']
