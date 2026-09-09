import pytest
from fastapi.testclient import TestClient
from app.config import Settings
from app.main import create_app

@pytest.fixture
def settings(tmp_path):
    return Settings(str(tmp_path/'trust.db'),'a'*40,'p'*40,'h'*40,rate_limit=1000)

@pytest.fixture
def app(settings):
    return create_app(settings)

@pytest.fixture
def client(app):
    with TestClient(app) as c:
        yield c
