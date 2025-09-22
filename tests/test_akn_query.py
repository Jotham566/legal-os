from __future__ import annotations

from fastapi.testclient import TestClient

from legal_os.main import create_app
from legal_os.settings import Settings
from legal_os.services.akn import transform_to_akn


def make_client():
    settings = Settings(env="test")
    app = create_app(settings)
    return TestClient(app)


def build_xml():
    payload = {
        "metadata": {"title": "Income Tax Act", "jurisdiction": "ke"},
        "content": [
            {"id": "sec1", "heading": "Short title", "text": "This Act may be cited as..."},
            {"id": "sec2", "heading": "Interpretation", "text": "In this Act..."},
            {"id": "sec3", "heading": "Application", "text": "This Act applies to..."},
        ],
    }
    return transform_to_akn(payload).decode("utf-8")


def test_xpath_query_returns_nodes_and_text():
    client = make_client()
    xml = build_xml()
    r = client.post("/api/v1/akn/xpath", json={"xml": xml, "query": "//akn:section/akn:heading/text()"})
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["results"][:2] == ["Short title", "Interpretation"]


def test_section_lookup_by_eid():
    client = make_client()
    xml = build_xml()
    r = client.post("/api/v1/akn/section", json={"xml": xml, "eid": "sec2"})
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["eid"] == "sec2"
    assert "Interpretation" in data["heading"]
    assert "<section" in data["xml"]


def test_navigation_neighbors():
    client = make_client()
    xml = build_xml()
    r = client.post("/api/v1/akn/nav", json={"xml": xml, "eid": "sec2"})
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["current_eid"] == "sec2"
    assert data["prev_eid"] == "sec1"
    assert data["next_eid"] == "sec3"
    assert "Interpretation" in data["heading"]
