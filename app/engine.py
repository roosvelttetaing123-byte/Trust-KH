"""Explainable passive triage. Does not fetch, visit, probe or execute submitted content.
No threat feed is enabled. Local fixture matches are ALWAYS labelled synthetic.
Community report counts are deliberately not an input to the risk engine.
"""
import hashlib
import hmac
import ipaddress
import re
from urllib.parse import urlsplit
from .qr import inspect_emv

RULE_VERSION = 'starter-rules.1'
FIXTURES = {'reward-check.test': 'SYNTHETIC investment/OTP demonstration',
            'parcel-fee.test': 'SYNTHETIC delivery-fee demonstration'}
URL_RE = re.compile(r'(?:https?://|hxxps?://)[^\s<>"\x00-\x1f]+', re.I)
PHONE_RE = re.compile(r'(?<!\w)(?:\+855|0)[\d .()-]{7,15}\d(?!\w)')
NEGATIVE_RE = re.compile(r'\b(?:never|do not|don.t|avoid|not to)\s+(?:\w+\s+){0,3}(?:share|send|give|tell|provide|enter)\b', re.I)
REQUEST_RE = re.compile(r'\b(?:send|share|give|tell|provide|enter)\b.{0,45}\b(?:otp|one.time (?:password|code)|password|pin)\b', re.I)
KH_REQUEST_RE = re.compile(r'(?:ផ្ញើ|ប្រាប់|ផ្តល់|បញ្ចូល).{0,25}(?:OTP|លេខសម្ងាត់|ពាក្យសម្ងាត់)', re.I)

def key_for(kind: str, value: str, secret: str) -> str:
    return hmac.new(secret.encode(), f'{kind}:{value}'.encode(), hashlib.sha256).hexdigest()

def clean_host(raw: str) -> tuple[str, dict]:
    raw = re.sub(r'^hxxp', 'http', raw, flags=re.I).replace('[.]', '.')
    if not re.match(r'^https?://', raw, re.I):
        if '://' in raw or raw.lower().startswith(('javascript:','data:','file:')):
            raise ValueError('Only http/https URLs are supported; they are never opened.')
        raw = 'https://' + raw
    try:
        parsed = urlsplit(raw)
        _ = parsed.port  # Validate invalid/out-of-range ports.
        host = (parsed.hostname or '').rstrip('.').lower().encode('idna').decode('ascii')
    except (ValueError, UnicodeError) as exc:
        raise ValueError('Invalid URL.') from exc
    if (not host or len(host)>253 or '%' in host or any(ord(c)<33 for c in raw)
            or not re.fullmatch(r'[a-z0-9.\-:]+', host)):
        raise ValueError('Invalid URL hostname.')
    local = host == 'localhost' or host.endswith(('.localhost','.local','.internal'))
    try:
        local = local or not ipaddress.ip_address(host).is_global
    except ValueError:
        pass
    return host, {'embedded_userinfo':bool(parsed.username is not None), 'local_address':local}

def synthetic_host(host: str) -> bool:
    # Keep reserved demonstration domains out of real-report aggregates.
    return host.endswith(('.test', '.invalid', '.example')) or host in {'example.com', 'example.net', 'example.org'}

def normalize_phone(value: str) -> str:
    digits = re.sub(r'\D','',value)
    if digits.startswith('0'):
        digits = '855' + digits[1:]
    if not digits.startswith('855') or len(digits) not in (11,12):
        raise ValueError('Use a Cambodian number in +855 or local 0 format. No owner lookup is performed.')
    return '+'+digits

def analyze(kind: str, text: str, secret: str) -> dict:
    indicators, signals, context = [], [], []
    seen = set()
    demo = False
    payment = None
    def add(kind, value, display):
        if (kind,value) not in seen and len(indicators)<20:
            seen.add((kind,value))
            indicators.append({'kind':kind, 'display':display, '_key':key_for(kind,value,secret)})
    def signal(rule, en, km, strength='caution', source='Local rules; not a verified threat feed'):
        if rule not in {s['rule_id'] for s in signals}:
            signals.append({'rule_id':rule,'strength':strength,'source':source,'en':en,'km':km})
    if kind == 'qr' and text.startswith('000201'):
        payment = inspect_emv(text)
        context.append('Only a limited EMV-style parser was run. No NBC or bank API was contacted.')
        # Exact payload HMAC permits private matching, not account attribution.
        add('qr_payload',text,'Payment QR • account details not retained')
        if not payment.get('structural_check_passed'):
            signal('qr_unverified','The payment QR could not be structurally confirmed. Verify it in your bank app.',
                   'មិនអាចផ្ទៀងផ្ទាត់ទម្រង់ QR បានទេ។ សូមផ្ទៀងផ្ទាត់ក្នុងកម្មវិធីធនាគារ។')
    elif kind in {'url','qr'}:
        host, flags = clean_host(text)
        demo = synthetic_host(host)
        add('domain',host,host.replace('.','[.]'))
        if host in FIXTURES:
            demo = True
            signal('synthetic_fixture','This matches a synthetic demonstration indicator. It is not a live threat finding.',
                   'នេះជាទិន្នន័យសម្រាប់សាកល្បង មិនមែនជាលទ្ធផលគំរាមកំហែងពិតទេ។', 'high', FIXTURES[host])
        if flags['embedded_userinfo']:
            signal('url_userinfo','The URL contains an account-style prefix that may disguise the actual destination.',
                   'តំណនេះមានបុព្វបទដែលអាចបំភាន់អាសយដ្ឋានគោលដៅ។')
        if flags['local_address']:
            context.append('Local/private address: no network request was made; no public reputation assessment is available.')
    elif kind == 'phone':
        value = normalize_phone(text)
        add('phone',value,value[:4]+' •••• '+value[-3:])
        context.append('No telephone owner, banking, or live reputation database is connected.')
    else:
        for match in URL_RE.finditer(text):
            try:
                host, flags = clean_host(match.group().rstrip('.,;!?)'))
                demo = demo or synthetic_host(host)
                add('domain',host,host.replace('.','[.]'))
                if host in FIXTURES:
                    demo = True
                    signal('synthetic_fixture','This matches a synthetic demonstration indicator. It is not a live threat finding.',
                           'នេះជាទិន្នន័យសម្រាប់សាកល្បង មិនមែនជាលទ្ធផលគំរាមកំហែងពិតទេ។','high',FIXTURES[host])
                if flags['embedded_userinfo']:
                    signal('url_userinfo','A link uses an account-style prefix. Inspect the actual domain.',
                           'តំណមានបុព្វបទដែលអាចបំភាន់អ្នក។ សូមពិនិត្យឈ្មោះដែនពិត។')
            except ValueError:
                pass
        for match in PHONE_RE.finditer(text):
            try:
                value = normalize_phone(match.group())
                add('phone',value,value[:4]+' •••• '+value[-3:])
            except ValueError:
                pass
        for handle in re.findall(r'(?:t\.me/|@)([a-zA-Z][a-zA-Z0-9_]{4,31})\b',text):
            add('handle',handle.lower(),'@'+handle[:2]+'•••'+handle[-2:])
        # Sentence-level exclusions reduce (but do not eliminate) warning-message false positives.
        for sentence in re.split(r'[!\n។]|(?<=[a-zA-Z])\.(?=\s)',text):
            if REQUEST_RE.search(sentence) and not NEGATIVE_RE.search(sentence):
                signal('credential_request','This text appears to ask you to share or enter an OTP, PIN, or password. Do not send credentials to a person or unverified page.',
                       'សារនេះហាក់ដូចជាស្នើសុំ OTP ឬលេខសម្ងាត់។ កុំផ្ញើព័ត៌មានសម្ងាត់ទៅអ្នកដទៃ ឬគេហទំព័រមិនស្គាល់។','high')
            if KH_REQUEST_RE.search(sentence) and not re.search(r'កុំ|មិនត្រូវ',sentence):
                signal('credential_request','This text appears to request credentials. Independently verify the sender; do not share secrets.',
                       'សារនេះហាក់ដូចជាស្នើសុំព័ត៌មានសម្ងាត់។ សូមផ្ទៀងផ្ទាត់អ្នកផ្ញើ និងកុំចែករំលែកលេខសម្ងាត់។','high')
        if re.search(r'\bguaranteed\b.{0,35}\b(?:profit|return|income)\b|ធានាប្រាក់ចំណេញ',text,re.I):
            signal('guaranteed_returns','A guaranteed-return claim deserves independent checking. The claim alone is not proof of fraud.',
                   'ការអះអាងធានាប្រាក់ចំណេញត្រូវការផ្ទៀងផ្ទាត់បន្ថែម។')
    verdict = 'high_risk' if any(s['strength']=='high' for s in signals) else ('caution' if signals else 'unknown')
    return {'verdict':verdict,'signals':signals,'indicators':indicators,'context':context,
            'payment':payment,'is_demo':demo,'rule_version':RULE_VERSION,
            'coverage':{'local_rules':True,'live_reputation':False,'website_visited':False,
                        'bank_account_verified':False,'screenshot_text_extraction':False},
            'notice':'Warning signs are not proof of fraud. Unknown never means safe. Results may be wrong.',
            'next_steps':['Do not share an OTP, PIN, password, or recovery phrase with another person.',
                          'Verify the request using an independently known contact or your official bank app.',
                          'If money was sent, contact your bank promptly and use the official police reporting channel.']}

def public_result(result: dict) -> dict:
    import copy
    obj = copy.deepcopy(result)
    for indicator in obj['indicators']:
        indicator.pop('_key',None)
    return obj
