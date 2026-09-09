"""PDF contract, local-resource boundaries and citizen control regressions."""
import io
import time
from unittest.mock import patch
import pytest
from pypdf import PdfReader
from app.pdf_summary import asset_fetcher, summary_html, render_summary, RENDER_SLOTS


def make_scan(client):
    return client.post('/api/scans',json={'kind':'message','text':'Send your OTP 990011 now. Visit https://reward-check.test/private-token?secret=private-value'}).json()


def pdf(client, scan, language='en', token=None):
    return client.get('/api/scans/'+scan['scan_id']+'/export?lang='+language,
                      headers={'Authorization':'Bearer '+(token or scan['access_token'])})


@pytest.mark.parametrize('language',['en','km','zh'])
def test_localized_real_pdf(client,language):
    scan=make_scan(client);r=pdf(client,scan,language)
    assert r.status_code==200,r.text[:100] if r.status_code!=200 else ''
    assert r.content.startswith(b'%PDF-')
    assert r.headers['content-type']=='application/pdf'
    assert r.headers['content-language']==language
    assert r.headers['cache-control']=='no-store'
    assert r.headers['content-disposition'].endswith(f'-{language}.pdf"')
    reader=PdfReader(io.BytesIO(r.content));assert 1<=len(reader.pages)<=2
    text=' '.join(p.extract_text() for p in reader.pages)
    for secret in ('990011','private-token','private-value',scan['access_token'],'token_hash','deletion_token'):
        assert secret not in text
    assert 'TRUST' in text
    assert not reader.attachments
    assert all(not p.get('/Annots') for p in reader.pages), 'No clickable submitted links'


def test_export_capability_and_expiry(client,app):
    scan=make_scan(client)
    assert pdf(client,scan,token='wrong').status_code==404
    assert client.get('/api/scans/'+scan['scan_id']+'/export').status_code==404
    app.state.scans.data[scan['scan_id']].expiry=time.time()-1
    assert pdf(client,scan).status_code==404


def test_export_default_khmer_and_invalid_language(client):
    scan=make_scan(client)
    r=client.get('/api/scans/'+scan['scan_id']+'/export',headers={'Authorization':'Bearer '+scan['access_token']})
    assert r.headers['content-language']=='km'
    assert pdf(client,scan,language='invalid').status_code==422


@pytest.mark.parametrize('url',['https://untrusted.example/image','file:///etc/passwd','data:text/html,test','trust-asset:unknown'])
def test_pdf_fetcher_refuses_unapproved_resources(url):
    with pytest.raises(ValueError):asset_fetcher(url)


def test_pdf_template_escapes_and_bounds_untrusted_display():
    raw='<img src="https://untrusted.example/collect">'
    html=summary_html({'verdict':'unknown','signals':[{'en':raw}],'indicators':[{'display':raw}],'payment':{'fields':{'account':'DO-NOT-EXPORT'}}},'en','test')
    assert raw not in html
    assert '&lt;img' in html
    assert 'DO-NOT-EXPORT' not in html
    assert '<a ' not in html
    assert '<script' not in html
    assert len(summary_html({'signals':[{'en':'x'*100000}]*1000},'en','test'))<20000


def test_pdf_capacity_is_bounded_and_released():
    assert RENDER_SLOTS.acquire(False)
    assert RENDER_SLOTS.acquire(False)
    try:
        with pytest.raises(RuntimeError,match='busy'):render_summary({},'en')
    finally:RENDER_SLOTS.release();RENDER_SLOTS.release()
    with pytest.raises(ValueError):render_summary({},'unsupported')
    assert render_summary({},'en').startswith(b'%PDF-')


def test_unavailable_pdf_is_not_a_fake_success(client):
    scan=make_scan(client)
    with patch('app.main.render_summary',side_effect=OSError('private-internal-path')):
        r=pdf(client,scan)
    assert r.status_code==503
    assert 'private-internal-path' not in r.text
    assert r.headers['content-type'].startswith('application/json')


def test_adaptive_inputs_and_accessible_status_in_source(client):
    html=client.get('/').text
    for id_ in ('check-url','check-phone','check-qr','image-file','check-status','qr-status','pdf-status'):
        assert id_ in html or id_ in client.get('/app.js').text
    assert 'type="tel"' in html and 'inputmode="url"' in html
    assert 'id="qr-input"' in html and 'id="qr-confirm"' in html
    assert 'role="status"' in html and 'role="alert"' in html
    assert 'hero-card' not in html
    assert 'prefers-reduced-motion' in client.get('/citizen.css').text
    assert 'citizen-i18n.js' in client.get('/sw.js').text
