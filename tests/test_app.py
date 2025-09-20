from fastapi.testclient import TestClient

from legal_os import create_app
from legal_os.settings import Settings


def test_health_endpoint():
    app = create_app()
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_config_endpoint_reads_env(monkeypatch):
    monkeypatch.setenv("ENV", "test")
    monkeypatch.setenv("DEBUG", "false")
    settings = Settings(env="test", debug=False)
    app = create_app(settings)
    client = TestClient(app)
    resp = client.get("/config")
    assert resp.status_code == 200
    data = resp.json()
    assert data["env"] == "test"
    assert data["debug"] is False
