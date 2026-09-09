from binascii import crc_hqx
import json
import pytest
from app.engine import analyze,public_result,normalize_phone,clean_host,key_for
from app.qr import inspect_emv

SECRET='test-secret'

@pytest.mark.parametrize('text',['Hello, how are you?','Never share your OTP with anyone.',"Do not send your password.","Don't give me your PIN."])
def test_ordinary_or_warning_text_is_unknown(text):
    assert analyze('message',text,SECRET)['verdict']=='unknown'

@pytest.mark.parametrize('text',['Please send your OTP now.','Enter your password on this page.','សូមផ្ញើ OTP មកខ្ញុំ។'])
def test_credential_request(text):
    r=analyze('message',text,SECRET)
    assert r['verdict']=='high_risk'
    assert any(s['rule_id']=='credential_request' for s in r['signals'])

def test_unknown_never_means_safe():
    r=analyze('url','https://ordinary-shop.test',SECRET)
    assert r['verdict']=='unknown'
    assert not r['coverage']['live_reputation']
    assert not r['coverage']['website_visited']
    assert 'score' not in r

def test_fixture_is_explicitly_synthetic():
    r=analyze('url','https://reward-check.test',SECRET)
    assert r['is_demo'] and r['verdict']=='high_risk'
    assert 'SYNTHETIC' in r['signals'][0]['source']

def test_lookalike_subdomain_does_not_match_exact_fixture():
    r=analyze('url','https://reward-check.test.other-domain.test',SECRET)
    assert r['verdict']=='unknown'

def test_sensitive_url_components_not_exposed():
    r=public_result(analyze('url','https://username:privatepassword@shop.test/reset/private-token?otp=112233#account',SECRET))
    value=json.dumps(r)
    for secret in ['privatepassword','private-token','112233','username','_key']:
        assert secret not in value
    assert r['verdict']=='caution'

def test_phone_normalization_and_masking():
    assert normalize_phone('012 345 678')=='+85512345678'
    assert normalize_phone('+855 12 345 678')=='+85512345678'
    r=public_result(analyze('phone','012345678',SECRET))
    assert '+85512345678' not in json.dumps(r)
    assert r['verdict']=='unknown'

@pytest.mark.parametrize('value',['file:///etc/passwd','javascript:alert(1)','data:text/html,test','https://host.test:99999'])
def test_unsupported_urls(value):
    with pytest.raises(ValueError): analyze('url',value,SECRET)

@pytest.mark.parametrize('value',['http://127.0.0.1','http://localhost','http://[::1]','http://169.254.169.254'])
def test_private_addresses_never_fetched(value):
    r=analyze('url',value,SECRET)
    assert not r['coverage']['website_visited']
    assert r['verdict']=='unknown'

def test_hmac_is_keyed_and_kind_separated():
    assert key_for('phone','012345678','one')!=key_for('phone','012345678','two')
    assert key_for('phone','012345678','one')!=key_for('handle','012345678','one')

def make_emv():
    payload='00020101021153038405802KH5909DEMO SHOP6005DEMOX6304'
    return payload+f'{crc_hqx(payload.encode(),0xFFFF):04X}'

def test_payment_crc_does_not_authenticate_anyone():
    r=inspect_emv(make_emv())
    assert r['crc_valid'] is True
    assert r['recipient_verified'] is False
    assert r['fields']['displayed_name']=='DEMO SHOP'
    a=analyze('qr',make_emv(),SECRET)
    assert a['verdict']=='unknown'
    assert not a['coverage']['bank_account_verified']

def test_invalid_crc_is_not_proof_of_fraud():
    r=inspect_emv(make_emv()[:-4]+'0000')
    assert not r['crc_valid']
    assert 'not proof of fraud' in r['error']

def test_non_ascii_qr_fails_explicitly_not_silently():
    assert inspect_emv('000201ហាង63040000')['supported'] is False


def test_reserved_unknown_domain_is_demo_without_a_threat_claim():
    for kind, text in [('url', 'https://ordinary-shop.test'), ('message', 'Visit https://ordinary-shop.test for details.')]:
        result = analyze(kind, text, SECRET)
        assert result['is_demo'] is True
        assert result['verdict'] == 'unknown'
        assert not result['signals']
