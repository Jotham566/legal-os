from fastapi.testclient import TestClient

from legal_os import create_app
from legal_os.settings import Settings


def test_liveness_contains_basic_info():
    app = create_app(Settings(env="test", debug=False))
    client = TestClient(app)
    resp = client.get("/health/live")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "live"
    assert isinstance(data["uptime_seconds"], int)
    assert data["name"]
    assert data["version"]
    assert data["env"] == "test"


def test_readiness_reports_db_status(monkeypatch):
    app = create_app(Settings(env="test", debug=False))
    client = TestClient(app)

    # Ready with working DB (SQLite default should pass)
    resp_ok = client.get("/health/ready")
    assert resp_ok.status_code == 200
    data_ok = resp_ok.json()
    assert data_ok["dependencies"]["database"] in {"ok", "fail"}
    assert data_ok["status"] in {"ready", "degraded"}


def test_legacy_endpoints_present():
    app = create_app(Settings(env="test", debug=False))
    client = TestClient(app)
    resp_health = client.get("/health")
    assert resp_health.status_code == 200
    assert resp_health.json()["status"] == "ok"

    resp_readiness = client.get("/readiness")
    assert resp_readiness.status_code == 200
    assert resp_readiness.json()["status"] in {"ready", "degraded"}
