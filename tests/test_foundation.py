"""Foundation regressions: implementation claims and evidence lifecycle."""
import time
import uuid

import pytest
from app.engine import analyze
from app.storage import Store, DEFAULT_ORG_ID

def test_manifest_truthful(client):
    response=client.get("/api/capabilities")
    assert response.status_code==200
    data=response.json()
    assert data["version"]=="0.2.0"
    assert data["production_ready"] is False
    assert data["external_requests"] is False
    assert "live_reputation" in data["not_implemented"]
    assert not set(data["working"]) & set(data["not_implemented"])
    assert response.headers["cache-control"]=="no-store"

def test_manifest_has_no_keys(client):
    text=client.get("/api/capabilities").text
    assert "deletion_token" not in text
    assert "TRUST_ADMIN_KEY" not in text

def test_demo_and_real_graph_never_merge(tmp_path):
    store=Store(str(tmp_path / "graph.db"))
    for demo in [True, False]:
        scan=analyze("url", "https://shared.example", "test-secret")
        scan["is_demo"]=demo  # Simulate records from both allowed datasets.
        receipt=store.report(scan,{"scan_id":uuid.uuid4().hex,"consent_version":"2026-09-09.v1","category":"other","channel":"web"},DEFAULT_ORG_ID)
        store.review(receipt["report_id"],"accepted","relevant_evidence",DEFAULT_ORG_ID)
    nodes=store.graph(DEFAULT_ORG_ID)["nodes"]
    assert len(nodes)==2
    assert {node["is_demo"] for node in nodes}=={True,False}
    assert all(node["reports"]==1 for node in nodes)

def test_expired_report_cannot_be_reviewed(tmp_path):
    store=Store(str(tmp_path / "expired.db"))
    receipt=store.report(analyze("url","https://example.com","test-secret"),
        {"scan_id":uuid.uuid4().hex,"consent_version":"2026-09-09.v1","category":"other","channel":"web"},DEFAULT_ORG_ID)
    with store.connect() as c:
        c.execute("UPDATE reports SET expires_at=?",(int(time.time())-10,))
    assert not store.review(receipt["report_id"],"accepted","relevant_evidence",DEFAULT_ORG_ID)
    assert store.graph(DEFAULT_ORG_ID)["nodes"]==[]

def test_project_studio_served(client):
    response=client.get("/project/")
    assert response.status_code==200
    assert "Project studio" in response.text
    assert "planned" in response.text.lower()

def test_no_vendor_script_on_home(client):
    text=client.get("/").text
    assert '<script src="http' not in text
    assert 'src="https://' not in text

def test_headline_and_project_link(client):
    text=client.get("/").text
    assert 'lang="km"' in text  # Khmer is the base language; en/zh are applied by i18n.js.
    assert "ពិនិត្យមុននឹងជឿ" in text
    assert 'href="/project/"' in text

def test_three_languages_offered(client):
    text=client.get("/").text
    for value in ('value="km"','value="en"','value="zh"'):
        assert value in text

def test_fonts_are_self_hosted(client):
    """Strict CSP allows font-src 'self' only, so the Khmer webfont must be local."""
    assert "fonts.googleapis.com" not in client.get("/style.css").text
    assert client.get("/fonts/kantumruy-pro-khmer.woff2").status_code==200

def test_openapi_version(client):
    assert client.get("/api/openapi.json").json()["info"]["version"]=="0.2.0"

# ---------- hosted demo mode ----------

@pytest.fixture
def demo_client(tmp_path):
    from fastapi.testclient import TestClient
    from app.config import Settings
    from app.main import create_app
    settings=Settings(str(tmp_path/"demo.db"),"h"*40,rate_limit=1000,demo=True,
                      allowed_origins=("https://demo.example",))
    with TestClient(app=create_app(settings),base_url="https://demo.example") as c:
        yield c

def test_demo_refuses_report_intake(demo_client):
    """The block must live in the server, so a hosted demo cannot collect real evidence."""
    scan=demo_client.post("/api/scans",json={"kind":"message","text":"Send your OTP to claim."}).json()
    response=demo_client.post("/api/reports",
        headers={"Authorization":"Bearer "+scan["access_token"]},
        json={"scan_id":scan["scan_id"],"consent":True,"consent_version":"2026-09-09.v1",
              "category":"other","channel":"web"})
    assert response.status_code==403
    assert "not collected" in response.json()["detail"]

def test_demo_still_explains_warning_signs(demo_client):
    """Turning off intake must not turn off the thing testers are being asked to judge."""
    result=demo_client.post("/api/scans",json={"kind":"message","text":"Send your OTP now."}).json()
    assert result["verdict"]=="high_risk"
    assert result["signals"]

def test_demo_advertises_its_own_limits(demo_client):
    caps=demo_client.get("/api/capabilities").json()
    assert caps["mode"]=="public_demo"
    assert caps["report_intake"] is False
    assert demo_client.get("/api/health").json()["report_intake"] is False

def test_demo_sends_hsts_and_keeps_strict_csp(demo_client):
    headers=demo_client.get("/").headers
    assert "max-age=31536000" in headers["strict-transport-security"]
    assert "frame-ancestors 'none'" in headers["content-security-policy"]

def test_demo_rejects_foreign_origin(demo_client):
    response=demo_client.post("/api/scans",json={"kind":"message","text":"Hello"},
                              headers={"Origin":"https://unrelated.test"})
    assert response.status_code==403

def test_local_mode_still_accepts_reports(client):
    """Demo mode must not silently disable intake for the local pilot build."""
    assert client.get("/api/capabilities").json()["report_intake"] is True
    scan=client.post("/api/scans",json={"kind":"message","text":"Send your OTP to claim."}).json()
    assert client.post("/api/reports",headers={"Authorization":"Bearer "+scan["access_token"]},
        json={"scan_id":scan["scan_id"],"consent":True,"consent_version":"2026-09-09.v1",
              "category":"other","channel":"web"}).status_code==201

def test_production_env_is_still_refused(monkeypatch,tmp_path):
    from app.config import Settings
    monkeypatch.setenv("TRUST_ENV","production")
    monkeypatch.setenv("TRUST_HMAC_KEY","h"*40)
    monkeypatch.setenv("TRUST_DB",str(tmp_path/"x.db"))
    with pytest.raises(RuntimeError,match="RELEASE_GATES"):
        Settings.from_env()

def test_demo_env_requires_an_https_origin(monkeypatch,tmp_path):
    from app.config import Settings
    monkeypatch.setenv("TRUST_ENV","demo")
    monkeypatch.setenv("TRUST_HMAC_KEY","h"*40)
    monkeypatch.setenv("TRUST_DB",str(tmp_path/"x.db"))
    monkeypatch.delenv("TRUST_ORIGIN",raising=False)
    with pytest.raises(RuntimeError,match="TRUST_ORIGIN"):
        Settings.from_env()
    monkeypatch.setenv("TRUST_ORIGIN","http://insecure.example")
    with pytest.raises(RuntimeError,match="https"):
        Settings.from_env()
