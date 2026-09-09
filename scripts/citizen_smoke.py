"""Citizen regression checks using synthetic inputs only.

Default: real HTTP + Chromium against a fresh temporary local service.
--adapter: offline DOM + TestClient bridge, for restricted authoring environments.
The adapter does NOT establish browser HTTP/CSP/service-worker behavior.
"""
from pathlib import Path
import argparse
import base64
import io
import json
import os
import re
import socket
import subprocess
import sys
import tempfile
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import qrcode
from fastapi.testclient import TestClient
from playwright.sync_api import sync_playwright
from app.main import create_app
from app.config import Settings

parser=argparse.ArgumentParser()
parser.add_argument('--adapter',action='store_true')
parser.add_argument('--out',default=str(ROOT/'artifacts/citizen'))
args=parser.parse_args();out=Path(args.out);out.mkdir(parents=True,exist_ok=True)

# Injected only by this test harness; production has no fake delays or test endpoints.
WRAP_FETCH='''
window.__holdMs=0;window.__failNext=false;window.__calls=[];
const realFetch=window.fetch.bind(window);
window.fetch=async(path,init={})=>{
 const isCheck=String(path)==='/api/scans'&&init.method==='POST';
 if(isCheck){window.__calls.push(String(path));if(window.__failNext){window.__failNext=false;throw Error('Synthetic network failure');}}
 const response=await realFetch(path,init);
 if(isCheck&&window.__holdMs)await new Promise(r=>setTimeout(r,window.__holdMs));
 return response;
};
'''
with tempfile.TemporaryDirectory() as tmp:
 process=None
 client=TestClient(create_app(Settings(str(Path(tmp)/'adapter.db'),'synthetic-ux-key-'*4,rate_limit=10000)))
 if not args.adapter:
  with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
  env={**os.environ,'TRUST_ENV':'test','TRUST_DB':str(Path(tmp)/'http.db'),'TRUST_HMAC_KEY':'synthetic-ux-key-'*4}
  process=subprocess.Popen([sys.executable,'-m','uvicorn','app.main:create_app','--factory','--host','127.0.0.1','--port',str(port),'--no-access-log'],cwd=ROOT,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  import httpx
  for _ in range(100):
   try:
    if httpx.get(f'http://127.0.0.1:{port}/api/health').status_code==200:break
   except httpx.HTTPError:pass
   time.sleep(.1)
  else:raise RuntimeError('Local HTTP service did not start')
 try:
  with sync_playwright() as p:
   executable=os.getenv('CHROMIUM_PATH')
   if not executable and Path('/usr/bin/chromium').exists():executable='/usr/bin/chromium'
   browser=p.chromium.launch(executable_path=executable,args=['--no-sandbox'])
   page=browser.new_page(viewport={'width':1280,'height':960},accept_downloads=True)
   page.set_default_timeout(12000);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   if args.adapter:
    static=ROOT/'app/static';html=(static/'index.html').read_text()
    html=re.sub(r'<link[^>]+>','',html).replace('<script type="module" src="/app.js"></script>','')
    css=(static/'style.css').read_text()+'\n'+(static/'citizen.css').read_text()
    for font in (static/'fonts').glob('*.woff2'):
     css=css.replace('/fonts/'+font.name,'data:font/woff2;base64,'+base64.b64encode(font.read_bytes()).decode())
    logo='data:image/svg+xml;base64,'+base64.b64encode((static/'icon.svg').read_bytes()).decode()
    html=html.replace('/icon.svg',logo).replace('</head>','<style>'+css+'</style></head>')
    js=(static/'i18n.js').read_text().replace('export const','const')+'\n'+(static/'citizen-i18n.js').read_text().replace('export const','const')+'\n'+(static/'app.js').read_text()
    js=re.sub(r'^import .*?;\n','',js,flags=re.M)
    js=re.sub(r"if\('serviceWorker'in navigator\)navigator.serviceWorker.register\('/sw.js'\).catch\(\(\)=>\{\}\);",'',js)
    def bridge(req):
     response=client.request(req['method'],req['path'],headers=req.get('headers',{}),content=base64.b64decode(req.get('body','')) or None)
     return {'status':response.status_code,'headers':dict(response.headers),'body':base64.b64encode(response.content).decode()}
    page.expose_function('__testApi',bridge);page.set_content(html)
    page.add_script_tag(content='''window.fetch=async(path,init={})=>{const bytes=init.body?new Uint8Array(await new Blob([init.body]).arrayBuffer()):new Uint8Array();let binary='';for(const byte of bytes)binary+=String.fromCharCode(byte);const r=await window.__testApi({path,method:init.method||'GET',headers:init.headers||{},body:btoa(binary)});return new Response(r.status===204?null:Uint8Array.from(atob(r.body),c=>c.charCodeAt(0)),{status:r.status,headers:r.headers});};''')
    page.add_script_tag(content=WRAP_FETCH);page.add_script_tag(content=js)
   else:
    page.add_init_script(WRAP_FETCH);page.goto(f'http://127.0.0.1:{port}',wait_until='networkidle')
   page.wait_for_function("document.querySelector('#run-check').getAttribute('aria-busy')==='false'")
   page.evaluate('document.fonts.ready');assert not page.locator('#result-panel').is_visible()
   page.screenshot(path=str(out/'home-km.png'),full_page=True)
   page.select_option('#language','en')
   page.locator('[data-kind="url"]').click()
   assert page.locator('#check-url').is_visible() and not page.locator('#check-text').is_visible()
   assert page.locator('#check-url').bounding_box()['height']<80
   page.locator('#check-url').fill('https://ordinary-shop.test/catalog')
   page.evaluate('window.__holdMs=800')
   page.locator('#run-check').click()
   assert page.locator('#run-check').is_disabled()
   assert page.locator('#check-button-label').inner_text()=='Checking…'
   assert page.locator('#check-status').inner_text()=='Checking…'
   page.screenshot(path=str(out/'checking.png'),full_page=True)
   page.locator('.verdict-label').wait_for();assert page.locator('.verdict-label').inner_text()=='Unknown — not verified'
   assert page.evaluate('window.__calls.length')==1
   # Clear and tab switches must win over a late response.
   page.evaluate('window.__holdMs=1200');page.locator('#run-check').click();page.locator('#clear-check').click()
   page.wait_for_timeout(1400);assert not page.locator('#result-panel').is_visible()
   page.locator('#check-url').fill('https://ordinary-shop.test/catalog');page.locator('#run-check').click()
   page.locator('[data-kind="phone"]').click();page.wait_for_timeout(1400)
   assert not page.locator('#result-panel').is_visible()
   assert page.locator('#check-phone').get_attribute('type')=='tel'
   # Failed check preserves input and exposes a persistent retry state.
   page.evaluate('window.__holdMs=0;window.__failNext=true')
   page.locator('[data-kind="message"]').click();page.locator('#check-text').fill('Send your OTP now.')
   page.locator('#run-check').click();page.locator('#check-error:not(.hidden)').wait_for()
   assert page.locator('#check-text').input_value()=='Send your OTP now.'
   assert page.locator('#check-button-label').inner_text()=='Try again'
   page.select_option('#language','km');assert 'មិនអាចតភ្ជាប់' in page.locator('#check-error').inner_text()
   page.locator('#run-check').click();page.locator('.verdict-label').wait_for()
   with page.expect_download() as event:page.locator('#export-summary').click()
   download=event.value;assert download.suggested_filename.endswith('-km.pdf');download.save_as(out/'browser-summary-km.pdf')
   page.locator('#pdf-status').filter(has_text='PDF').wait_for()
   page.screenshot(path=str(out/'result-km.png'),full_page=True)
   page.select_option('#language','en')
   # The real existing QR decoder, not a stub.
   page.locator('[data-kind="qr"]').click()
   assert page.locator('#image-file').is_visible()
   buffer=io.BytesIO();qrcode.make('https://ordinary-shop.test/catalog').save(buffer,format='PNG')
   page.locator('#image-file').set_input_files({'name':'synthetic-qr.png','mimeType':'image/png','buffer':buffer.getvalue()})
   page.locator('#canvas-wrap:not(.hidden)').wait_for();page.locator('#decode-qr').click()
   page.wait_for_function("document.querySelector('#check-qr').value.includes('ordinary-shop.test')")
   assert not page.locator('#qr-confirm').is_checked()
   page.locator('#run-check').click();assert page.locator('#check-error').is_visible()
   page.locator('#qr-confirm').check();page.locator('#run-check').click();page.locator('.verdict-label').wait_for()
   page.screenshot(path=str(out/'qr-upload.png'),full_page=True)
   page.locator('#remove-image').click();assert not page.locator('#canvas-wrap').is_visible()
   assert page.locator('#check-qr').input_value()==''
   page.locator('#image-file').set_input_files({'name':'invalid.png','mimeType':'image/png','buffer':b'not an image'})
   page.locator('#qr-error:not(.hidden)').wait_for()
   assert not page.locator('#canvas-wrap').is_visible()
   # Resize and keyboard-friendly controls. PDF language picker follows the UI.
   for language in ('km','en','zh'):
    page.select_option('#language',language)
    for width in (320,390,768,1280):
     page.set_viewport_size({'width':width,'height':900})
     assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),(language,width,'overflow')
   page.select_option('#language','km');page.set_viewport_size({'width':390,'height':844})
   page.locator('[data-kind="url"]').click();page.evaluate('scrollTo(0,0)');page.wait_for_timeout(200);page.screenshot(path=str(out/'mobile-link-km.png'),full_page=True)
   page.emulate_media(reduced_motion='reduce')
   assert page.evaluate("getComputedStyle(document.querySelector('.working-mark'),'::before').animationName")=='none'
   if not args.adapter:
    assert 'frame-ancestors' in page.request.get(f'http://127.0.0.1:{port}/').headers['content-security-policy']
    page.wait_for_function('navigator.serviceWorker.controller!==null')
    cached=page.evaluate('''async()=>{const all=[];for(const k of await caches.keys()){for(const r of await(await caches.open(k)).keys())all.push(new URL(r.url).pathname);}return all;}''')
    assert '/citizen.css' in cached and not any(path.startswith('/api/') for path in cached)
   assert not errors,errors
   (out/'test-results.json').write_text(json.dumps({'method':'offline DOM + TestClient' if args.adapter else 'HTTP + Chromium','javascript_errors':errors,'checks':['adaptive inputs','visible QR upload and actual decode','QR confirmation','PDF download in Khmer','loading/duplicate suppression','late-response cancellation','persistent localized error + retry','invalid image','three languages at four widths','reduced motion'],'service_worker':'not tested in adapter' if args.adapter else 'static-only cache inspected'},indent=2))
   print((out/'test-results.json').read_text());browser.close()
 finally:
  client.close()
  if process:process.terminate();process.wait(timeout=10)
