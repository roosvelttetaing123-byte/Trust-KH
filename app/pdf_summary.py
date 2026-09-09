"""Minimized citizen PDF summaries. No remote URLs, raw inputs, or stored files.

Only a fixed template and explicitly allowlisted bundled assets reach WeasyPrint.
The authenticated route passes public_result(), never a message or capability token.
"""
from datetime import datetime, timedelta, timezone
from html import escape
from pathlib import Path
from threading import BoundedSemaphore

RENDER_SLOTS = BoundedSemaphore(2)
STATIC = Path(__file__).parent / 'static'
ASSETS = {
    'trust-asset:logo': (STATIC / 'icon.svg', 'image/svg+xml'),
    'trust-asset:khmer': (STATIC / 'fonts/kantumruy-pro-khmer.woff2', 'font/woff2'),
    'trust-asset:latin': (STATIC / 'fonts/kantumruy-pro-latin.woff2', 'font/woff2'),
}
COPY = {
    'en': {
        'title': 'Check summary', 'generated': 'Generated', 'reference': 'Reference',
        'high_risk': 'Strong warning signs', 'caution': 'Use caution', 'unknown': 'Unknown — not verified',
        'notice': 'Warning signs are not proof of fraud. Unknown does not mean safe. Results may be wrong.',
        'reasons': 'Why this result?', 'none': 'No warning rule matched. This does not establish safety.',
        'next': 'What to do next', 'steps': [
            'Do not share an OTP, PIN, password or recovery phrase with another person.',
            'Verify through an independently known contact or your official bank app.',
            'If money was sent, contact your bank promptly and use the official police reporting channel.'
        ],
        'indicators': 'Minimized details', 'coverage': 'What was and was not checked',
        'limits': 'Basic local rules only. No live threat feed, bank verification, website visit or recipient-identity check.',
        'qr': 'QR decoding or checksum integrity does not verify a recipient, account owner or payment.',
        'footer': 'Check summary only — not a certificate or an official complaint.',
        'privacy': 'No original messages, images, passwords or access tokens are included. Preserve original evidence separately. No complaint has been submitted.',
        'demo': 'SYNTHETIC DEMONSTRATION — NOT A LIVE THREAT', 'version': 'Rule version', 'page': 'Page'
    },
    'km': {
        'title': 'សេចក្ដីសង្ខេបលទ្ធផលពិនិត្យ', 'generated': 'កាលបរិច្ឆេទបង្កើត', 'reference': 'លេខយោង',
        'high_risk': 'រកឃើញសញ្ញាព្រមានខ្លាំង', 'caution': 'សូមប្រុងប្រយ័ត្ន', 'unknown': 'មិនទាន់អាចបញ្ជាក់បាន',
        'notice': 'សញ្ញាព្រមានមិនមែនជាភស្តុតាងថាជាការឆបោកទេ។ លទ្ធផលមិនច្បាស់ មិនមានន័យថាមានសុវត្ថិភាពទេ។ លទ្ធផលអាចមានកំហុស។',
        'reasons': 'មូលហេតុនៃលទ្ធផលនេះ', 'none': 'ការពិនិត្យនេះមិនបានរកឃើញសញ្ញាព្រមានទេ។ នេះមិនបញ្ជាក់ថាមានសុវត្ថិភាពឡើយ។',
        'next': 'អ្វីដែលគួរធ្វើបន្ទាប់', 'steps': [
            'កុំប្រាប់លេខកូដ OTP លេខ PIN ពាក្យសម្ងាត់ ឬឃ្លាស្ដារគណនីទៅអ្នកដទៃ។',
            'ផ្ទៀងផ្ទាត់តាមលេខទំនាក់ទំនងដែលអ្នកស្គាល់ ឬកម្មវិធីធនាគារផ្លូវការ។',
            'បើបានផ្ញើប្រាក់ សូមទាក់ទងធនាគារជាបន្ទាន់ ហើយប្រើប្រព័ន្ធរាយការណ៍ផ្លូវការរបស់នគរបាល។'
        ],
        'indicators': 'ព័ត៌មានសង្ខេបដែលបានពិនិត្យ', 'coverage': 'វិសាលភាព និងដែនកំណត់នៃការពិនិត្យ',
        'limits': 'ប្រើតែការពិនិត្យមូលដ្ឋាន។ មិនមានទិន្នន័យគំរាមកំហែងផ្ទាល់ មិនពិនិត្យធនាគារ មិនបើកគេហទំព័រ និងមិនផ្ទៀងផ្ទាត់អត្តសញ្ញាណអ្នកទទួលប្រាក់ទេ។',
        'qr': 'ការអានកូដ QR ឬលេខត្រួតពិនិត្យត្រឹមត្រូវ មិនបញ្ជាក់អត្តសញ្ញាណអ្នកទទួលប្រាក់ ម្ចាស់គណនី ឬការទូទាត់ទេ។',
        'footer': 'សេចក្ដីសង្ខេបប៉ុណ្ណោះ — មិនមែនជាវិញ្ញាបនបត្រ ឬពាក្យបណ្ដឹងផ្លូវការទេ។',
        'privacy': 'មិនរួមបញ្ចូលសារដើម រូបភាព លេខសម្ងាត់ ឬលេខកូដចូលប្រើទេ។ សូមរក្សាភស្តុតាងដើមដោយឡែក។ មិនមានការដាក់ពាក្យបណ្ដឹងណាមួយទេ។',
        'demo': 'ទិន្នន័យសាកល្បង — មិនមែនជាការគំរាមកំហែងពិតទេ', 'version': 'កំណែការពិនិត្យ', 'page': 'ទំព័រ'
    },
    'zh': {
        'title': '检查结果摘要', 'generated': '生成时间', 'reference': '参考编号',
        'high_risk': '存在明显警示信号', 'caution': '请谨慎', 'unknown': '未知 — 尚未核实',
        'notice': '警示信号并非欺诈证据。未知不等于安全，结果可能有误。',
        'reasons': '判断依据', 'none': '未命中警示规则。这并不能证明安全。',
        'next': '接下来该怎么做', 'steps': ['切勿向他人透露验证码、PIN、密码或助记词。', '通过已知的联系方式或官方银行应用自行核实。', '若已转账，请尽快联系银行并使用警方官方渠道报案。'],
        'indicators': '最小化信息', 'coverage': '检查范围与限制',
        'limits': '仅使用基本规则。无实时情报、银行核验、网站访问或收款人身份核验。',
        'qr': '成功读取二维码或校验和正确并不能核实收款人、账户归属或付款。',
        'footer': '仅为检查摘要 — 并非证书或正式报案。',
        'privacy': '不包含原始信息、图片、密码或访问令牌。请单独保留原始证据。未提交任何正式报案。',
        'demo': '合成演示数据 — 并非真实威胁', 'version': '规则版本', 'page': '页'
    },
}


def asset_fetcher(url, *args, **kwargs):
    """Reject even file/data URLs unless they match a fixed, bundled resource."""
    if url not in ASSETS:
        raise ValueError('PDF resource is not allowlisted')
    path, mime = ASSETS[url]
    return {'string': path.read_bytes(), 'mime_type': mime}


def text(value, limit=500):
    # Bounded, escaped text only. Bidi controls are unnecessary in these locales.
    value = ''.join(c for c in str(value)[:limit] if c not in '\u202a\u202b\u202c\u202d\u202e\u2066\u2067\u2068\u2069')
    return escape(value)


def summary_html(result: dict, language: str, reference: str) -> str:
    if language not in COPY:
        raise ValueError('Unsupported summary language')
    c = COPY[language]
    verdict = result.get('verdict', 'unknown')
    if verdict not in ('high_risk', 'caution', 'unknown'):
        verdict = 'unknown'
    timestamp = datetime.now(timezone(timedelta(hours=7))).strftime('%Y-%m-%d %H:%M UTC+07:00')
    reasons = ''.join('<li>' + text(s.get(language) or s.get('en', ''), 800) + '</li>'
                      for s in result.get('signals', [])[:12]) or '<li>' + c['none'] + '</li>'
    # public_result omits private keys; still select explicit fields instead of serializing it.
    indicators = ''.join('<li>' + text(i.get('display', ''), 300) + '</li>'
                         for i in result.get('indicators', [])[:20])
    indicator_section = ('<h2>' + c['indicators'] + '</h2><ul class="indicators">' + indicators + '</ul>') if indicators else ''
    demo = '<p class="demo">' + c['demo'] + '</p>' if result.get('is_demo') else ''
    return f'''<!doctype html><html lang="{language}"><head><meta charset="utf-8">
<title>Trust.kh — {c['title']}</title><style>
@font-face{{font-family:TrustKhmer;src:url('trust-asset:khmer');font-weight:100 900}}
@font-face{{font-family:TrustLatin;src:url('trust-asset:latin');font-weight:100 900}}
@page{{size:A4;margin:16mm 17mm 19mm;@bottom-left{{content:"TRUST.KH / {c['page']} " counter(page);font:9pt TrustLatin,TrustKhmer,sans-serif;color:#536373}}}}
body{{font-family:TrustKhmer,TrustLatin,'Noto Sans CJK SC',sans-serif;font-size:11pt;line-height:1.7;color:#223447}}
html[lang=km] body{{font-size:12pt;line-height:1.85}}
header{{border-bottom:2px solid #1b63c4;padding-bottom:10pt;margin-bottom:14pt}}
header img{{width:38pt;vertical-align:middle;margin-right:10pt}}.brand{{font:700 21pt TrustLatin,sans-serif;color:#1b63c4}}.brand span{{color:#c2570b}}
h1{{font-size:21pt;margin:10pt 0 4pt;line-height:1.6}}h2{{font-size:13pt;color:#164d90;margin:12pt 0 5pt;break-after:avoid}}
p{{margin:5pt 0}}li{{margin:3pt 0;overflow-wrap:anywhere;break-inside:avoid}}ul,ol{{padding-left:18pt;margin:4pt 0}}
.meta,.footnote{{font-size:9pt;color:#536373}}.verdict{{padding:10pt 13pt;background:#eef4fc;border-left:4pt solid #1b63c4;margin:12pt 0;break-inside:avoid}}
.high_risk{{background:#fff0ef;border-color:#b3261e}}.caution{{background:#fff7e5;border-color:#916000}}.verdict strong{{font-size:15pt}}
.demo{{font-weight:700;color:#9d3d08}}.indicators{{font-size:10pt;word-break:break-all}}.privacy{{border-top:1px solid #ccd6e0;padding-top:8pt;margin-top:14pt}}
</style></head><body><header><img src="trust-asset:logo" alt=""><span class="brand">TRUST<span>.KH</span></span></header>
<h1>{c['title']}</h1><p class="meta">{c['generated']}: {timestamp}<br>{c['reference']}: {text(reference, 24)} · {c['version']}: {text(result.get('rule_version',''), 80)}</p>
{demo}<div class="verdict {verdict}"><strong>{c[verdict]}</strong><p>{c['notice']}</p></div>
<h2>{c['reasons']}</h2><ul>{reasons}</ul><h2>{c['next']}</h2><ol>{''.join('<li>'+v+'</li>' for v in c['steps'])}</ol>
{indicator_section}<h2>{c['coverage']}</h2><p>{c['limits']}</p>{'<p>'+c['qr']+'</p>' if result.get('payment') else ''}
<div class="privacy"><p><strong>{c['footer']}</strong></p><p class="footnote">{c['privacy']}</p><p class="footnote">hotline.police.gov.kh</p></div></body></html>'''


def render_summary(result: dict, language='km', reference='') -> bytes:
    """Render in memory; bound simultaneous work. Caller handles unavailable errors."""
    if not RENDER_SLOTS.acquire(blocking=False):
        raise RuntimeError('PDF renderer busy')
    try:
        if any(not path.is_file() for path, _ in ASSETS.values()):
            raise OSError("Bundled PDF asset is missing")
        from weasyprint import HTML
        from weasyprint.text.fonts import FontConfiguration
        return HTML(string=summary_html(result, language, reference), url_fetcher=asset_fetcher).write_pdf(
            font_config=FontConfiguration())
    finally:
        RENDER_SLOTS.release()
