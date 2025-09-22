import pytest
from fastapi.testclient import TestClient

from legal_os.main import app


client = TestClient(app)


def test_external_resolve_json_basic():
    payload = {
        "content": [
            {"text": "According to section 5 of the Income Tax Act, taxpayers must file returns."},
            {"text": "See Smith v. Republic [2020] eKLR for precedent."},
        ]
    }
    resp = client.post("/api/v1/structure/external/resolve/json", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "refs" in data and "metrics" in data
    refs = data["refs"]
    assert any("income tax act" in r["text"].lower() for r in refs)
    assert any("v." in r["text"] for r in refs)
    metrics = data["metrics"]
    assert metrics["total"] >= 2
    assert 0 <= metrics["resolution_rate"] <= 1


def test_external_resolve_xml_basic():
    xml = """
    <akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
      <act>
        <body>
          <section eId="sec_1">
            <num>1</num>
            <heading>Preliminary</heading>
            <paragraph>
              <content>Refer to section 5 of the Income Tax Act and the case of Smith v. Republic [2020] eKLR.</content>
            </paragraph>
          </section>
        </body>
      </act>
    </akomaNtoso>
    """
    resp = client.post("/api/v1/structure/external/resolve/xml", json={"xml": xml})
    assert resp.status_code == 200
    data = resp.json()
    assert data["metrics"]["total"] >= 1
    # case should be detected and probably resolved to a placeholder canonical URI
    case_refs = [r for r in data["refs"] if r["kind"] == "case"]
    assert case_refs
    # statute likely resolved for Income Tax Act
    stat_refs = [r for r in data["refs"] if r["kind"] == "statute"]
    assert stat_refs or any("income tax act" in r["text"].lower() for r in data["refs"])
