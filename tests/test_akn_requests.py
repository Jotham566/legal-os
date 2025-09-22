import pytest
from fastapi.testclient import TestClient

from legal_os.main import create_app
from legal_os.settings import Settings


def make_client():
    settings = Settings(env="test")
    app = create_app(settings)
    return TestClient(app)


def test_akn_transform_minimal():
    client = make_client()
    payload = {
        "metadata": {"title": "Income Tax Act", "jurisdiction": "ke"},
        "content": [
            {"id": "sec1", "heading": "Short title", "text": "This Act may be cited as..."},
            {"id": "sec2", "heading": "Interpretation", "text": "In this Act..."},
        ],
    }
    r = client.post("/api/v1/akn/transform", json=payload)
    assert r.status_code == 200, r.text
    data = r.json()
    assert "<?xml" in data["xml"]
    assert "akomaNtoso" in data["xml"]
    assert "Short title" in data["xml"]


def test_akn_transform_handles_empty_fields():
    client = make_client()
    r = client.post("/api/v1/akn/transform", json={})
    assert r.status_code == 200
    data = r.json()
    assert "akomaNtoso" in data["xml"]


def test_akn_transform_invalid_xml_error(monkeypatch):
    client = make_client()
    import legal_os.routers.akn as akn_router

    def bad_transform(doc):
        return b"<akomaNtoso><act><body><section>"

    monkeypatch.setattr(akn_router, "transform_to_akn", bad_transform)
    r = client.post("/api/v1/akn/transform", json={"metadata": {}, "content": []})
    assert r.status_code == 400
    assert "Invalid Akoma Ntoso XML" in r.text
