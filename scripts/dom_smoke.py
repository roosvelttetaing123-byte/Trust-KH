"""Offline DOM/real-handler adapter test. Does not test HTTP navigation, CSP or service workers."""
from pathlib import Path
import sys, tempfile, base64, json, re
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root))
from fastapi.testclient import TestClient
from app.main import create_app
from app.config import Settings
from playwright.sync_api import sync_playwright
out=root/'artifacts';out.mkdir(exist_ok=True)
html=(root/'app/static/index.html').read_text()
html=re.sub(r'<link[^>]+>', '', html)
html=html.replace('</head>','<style>'+(root/'app/static/style.css').read_text()+'</style></head>')
html=html.replace('<script type="module" src="/app.js"></script>','')
js=(root/'app/static/i18n.js').read_text().replace('export const','const')+'\n'+(root/'app/static/app.js').read_text().replace("import {km,resultCopy} from './i18n.js';",'')
js=re.sub(r"if\('serviceWorker'in navigator\)navigator.serviceWorker.register\('/sw.js'\).catch\(\(\)=>\{\}\);",'',js)
with tempfile.TemporaryDirectory() as td, TestClient(create_app(Settings(td+'/db.sqlite','a'*40,'p'*40,'h'*40,rate_limit=1000))) as client, sync_playwright() as p:
    def bridge(req):
        response=client.request(req['method'],req['path'],headers=req.get('headers',{}),content=base64.b64decode(req['body']) if req.get('body') else None)
        return {'status':response.status_code,'headers':dict(response.headers),'body':base64.b64encode(response.content).decode()}
    browser=p.chromium.launch(executable_path=__import__('os').getenv('CHROMIUM_PATH','/usr/bin/chromium'),args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':1440,'height':1000},device_scale_factor=1)
    page.set_default_timeout(6000)
    errors=[];page.on('pageerror', lambda e: errors.append(str(e)))
    page.expose_function('__testApi', bridge)
    page.set_content(html)
    page.add_script_tag(content="""window.fetch=async (path, init={})=>{if(!path.startsWith('/api/'))throw Error('Unexpected path');const raw=init.body?await new Blob([init.body]).arrayBuffer():new ArrayBuffer(0);const body=btoa(String.fromCharCode(...new Uint8Array(raw)));const r=await window.__testApi({path,method:init.method||'GET',headers:init.headers||{},body});const bytes=Uint8Array.from(atob(r.body),x=>x.charCodeAt(0));return new Response(r.status===204?null:bytes,{status:r.status,headers:r.headers});};""")
    page.add_script_tag(content=js)
    page.screenshot(path=str(out/'desktop-home.png'),full_page=True)
    page.click('[data-example="unknown"]'); page.click('#run-check')
    page.get_by_text('Unknown — not verified',exact=True).wait_for()
    page.click('[data-example="otp"]');page.click('#run-check')
    page.get_by_text('Strong warning signs',exact=True).wait_for()
    page.locator('.report-form summary').click();page.locator('#report-consent').check();page.click('#submit-report')
    page.locator('#save-receipt').wait_for()
    page.click('[data-page="analyst"]'); page.fill('#analyst-key','a'*40);page.click('#load-analyst')
    page.locator('[data-review="accepted"]').first.wait_for();page.locator('[data-review="accepted"]').first.click()
    page.locator('.graph-node').first.wait_for()
    page.fill('#analyst-key','');page.screenshot(path=str(out/'analyst.png'),full_page=True)
    page.click('#lock-analyst');assert not page.locator('#analyst-content').is_visible()
    page.click('[data-page="pulse"]');page.fill('#pulse-key','p'*40);page.click('#load-pulse')
    page.get_by_text('Signals, with boundaries.',exact=True).wait_for();page.fill('#pulse-key','')
    page.screenshot(path=str(out/'pulse.png'),full_page=True)
    page.click('[data-page="check"]');page.click('#language'); assert page.locator('html').get_attribute('lang')=='km'
    page.screenshot(path=str(out/'khmer.png'),full_page=True)
    page.click('#language');page.set_viewport_size({'width':390,'height':844})
    page.screenshot(path=str(out/'mobile-result.png'),full_page=True)
    assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth'), 'mobile overflow'
    assert not errors, errors
    browser.close()
print(json.dumps({'ui_method':'offline DOM with in-process real FastAPI handler adapter','ui_flows':['unknown check','warning check','consented report','analyst review','graph view','analyst lock','aggregate role','Khmer toggle','390px overflow check'],'javascript_errors':errors,'http_navigation':'NOT validated by this adapter; run browser_smoke.py on an unrestricted local development browser','service_worker':'NOT validated by this adapter','screenshots':str(out)},indent=2))
