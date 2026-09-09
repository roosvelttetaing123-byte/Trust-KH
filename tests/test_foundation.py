from pathlib import Path
import pytest
from app.capabilities import manifest, VERSION


def test_capabilities_are_explicit(client):
    r = client.get('/api/capabilities')
    assert r.status_code == 200
    assert r.json()['production_ready'] is False
    assert r.json()['external_requests'] is False
    assert r.headers['cache-control'] == 'no-store'


@pytest.mark.parametrize('feature', [
    'screenshot_text_extraction', 'named_identity_and_tenant_isolation',
    'approved_publication_snapshots',
])
def test_planned_features_not_promoted(feature):
    assert manifest()['features'][feature] == 'planned'


def test_no_bank_or_live_feed_claim(client):
    features = client.get('/api/capabilities').json()['features']
    assert features['live_reputation'] == 'not_configured'
    assert features['bank_or_government_api'] == 'not_integrated'


def test_manifest_does_not_leak_keys(client, settings):
    content = client.get('/api/capabilities').text
    for secret in (settings.admin_key, settings.pulse_key, settings.hmac_key):
        assert secret not in content


def test_openapi_matches_version(client):
    assert client.get('/api/openapi.json').json()['info']['version'] == VERSION


def test_studio_is_clearly_a_preview(client):
    r = client.get('/studio.html')
    assert r.status_code == 200
    assert 'SYNTHETIC DATA' in r.text
    assert 'Design preview' in r.text


def test_studio_assets_are_available(client):
    for asset in ('/studio.css','/studio.js'):
        assert client.get(asset).status_code == 200
