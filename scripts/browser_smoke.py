"""Optional UI smoke test. Requires Playwright + a Chromium binary and a running local app.
Use only the local starter; the script never visits submitted test URLs.
"""
import json
from pathlib import Path
import os
from playwright.sync_api import sync_playwright

root=Path(__file__).resolve().parents[1]
keys=dict(line.split('=',1) for line in (root/'.env').read_text().splitlines() if '=' in line)
out=Path(os.getenv('TRUST_SCREENSHOTS',str(root/'artifacts')))
out.mkdir(exist_ok=True,parents=True)
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path=os.getenv('CHROMIUM_PATH','/usr/bin/chromium'),args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':1440,'height':1100},device_scale_factor=1)
    failures=[]
    page.on('pageerror',lambda error:failures.append(str(error)))
    page.goto('http://127.0.0.1:8000/',wait_until='networkidle')
    page.screenshot(path=str(out/'desktop-home.png'),full_page=True)
    assert page.locator('html').get_attribute('lang')=='km', 'Khmer is the base language'
    page.select_option('#language','en')  # English assertions below need the English dictionary.
    page.click('[data-example="unknown"]');page.click('#run-check')
    page.get_by_text('Unknown — not verified',exact=True).wait_for()
    page.click('[data-example="otp"]');page.click('#run-check')
    page.get_by_text('Strong warning signs',exact=True).wait_for()
    with page.expect_download() as download:
        page.click('#export-summary')
    assert download.value.suggested_filename=='trust-kh-review-summary.zip'
    page.locator('.report-form summary').click()
    page.locator('#report-consent').check()
    page.click('#submit-report')
    page.locator('#save-receipt').wait_for()
    page.click('[data-page="analyst"]')
    page.fill('#analyst-key',keys['TRUST_ADMIN_KEY'])
    page.click('#load-analyst')
    page.locator('[data-review="accepted"]').first.wait_for()
    page.locator('[data-review="accepted"]').first.click()
    page.locator('.graph-node').first.wait_for()
    page.click('#lock-analyst')
    assert not page.locator('#analyst-content').is_visible()
    page.click('[data-page="pulse"]')
    page.fill('#pulse-key',keys['TRUST_PULSE_KEY'])
    page.click('#load-pulse')
    page.get_by_text('Signals, with boundaries.',exact=True).wait_for()
    page.click('#lock-pulse')
    page.click('[data-page="check"]')
    page.select_option('#language','km')
    assert page.locator('html').get_attribute('lang')=='km'
    page.get_by_text('មានសញ្ញាព្រមានខ្លាំង',exact=True).wait_for()
    page.screenshot(path=str(out/'khmer-result.png'),full_page=True)
    page.select_option('#language','zh')
    assert page.locator('html').get_attribute('lang')=='zh'
    page.get_by_text('存在明显警示信号',exact=True).wait_for()
    page.screenshot(path=str(out/'chinese-result.png'),full_page=True)
    page.select_option('#language','en')
    page.set_viewport_size({'width':390,'height':844})
    page.screenshot(path=str(out/'mobile-result.png'),full_page=True)
    assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
    page.set_viewport_size({'width':1440,'height':1100})
    page.click('#clear-check')
    page.screenshot(path=str(out/'desktop-home.png'),full_page=True)
    # Static app shell can be read offline, but API results must not be cached.
    keys_cached=page.evaluate("async () => {const names=await caches.keys(); const urls=[]; for(const n of names){const c=await caches.open(n);for(const r of await c.keys())urls.push(new URL(r.url).pathname);}return urls;}")
    assert not any(url.startswith('/api/') for url in keys_cached)
    assert not failures,failures
    browser.close()
print(json.dumps({'ui_smoke':'passed','javascript_errors':0,'mobile_horizontal_overflow':False,'api_cache_entries':0,'screenshots':str(out)},indent=2))
