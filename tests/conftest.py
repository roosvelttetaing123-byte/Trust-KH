import pytest
from fastapi.testclient import TestClient
from app.accounts import Directory
from app.config import Settings
from app.identity import totp_now
from app.main import create_app
from app.storage import Store, DEFAULT_ORG_ID

PASSWORD = 'correct-horse-battery-staple'


@pytest.fixture
def settings(tmp_path):
    return Settings(str(tmp_path/'trust.db'), 'h'*40, rate_limit=1000)


@pytest.fixture
def app(settings):
    return create_app(settings)


@pytest.fixture
def client(app):
    with TestClient(app) as c:
        yield c


@pytest.fixture
def directory(app):
    return app.state.directory


@pytest.fixture
def make_staff(directory):
    """Create an account and return everything needed to sign in as it."""
    def _make(email='analyst@pilot.test', role='analyst', org_id=DEFAULT_ORG_ID, name='Test Analyst'):
        return directory.create_staff(org_id, email, name, PASSWORD, role)
    return _make


@pytest.fixture
def sign_in(client, make_staff):
    """Complete password + TOTP and return a bearer token for a fully authenticated session."""
    def _sign_in(email='analyst@pilot.test', role='analyst', org_id=DEFAULT_ORG_ID):
        account = make_staff(email=email, role=role, org_id=org_id)
        token = client.post('/api/auth/login', json={'email': email, 'password': PASSWORD}).json()['session']
        code = totp_now(account['totp_secret'])
        assert client.post('/api/auth/mfa', json={'code': code},
                           headers={'Authorization': 'Bearer ' + token}).status_code == 200
        return token
    return _sign_in


@pytest.fixture
def auth_header(sign_in):
    def _header(**kwargs):
        return {'Authorization': 'Bearer ' + sign_in(**kwargs)}
    return _header
