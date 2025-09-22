import pytest
from fastapi.testclient import TestClient

from legal_os.main import app

client = TestClient(app)


def test_validate_json_scores_and_issues():
    payload = {
        "content": [
            {"id": "p1", "heading": "Part I - General"},
            {"id": "c1", "heading": "Chapter 1 — Preliminary"},
            {"id": "s1", "heading": "Section 1 Short title"},
            {"id": "s2", "heading": "Section 2 Interpretation"},
        ]
    }
    r = client.post("/api/v1/structure/validate/json", json=payload)
    assert r.status_code == 200, r.text
    data = r.json()
    m = data["metrics"]
    # Bounds
    for k, v in m.items():
        assert 0.0 <= v <= 1.0
    # With both mandatory headings present, expect no missing_mandatory issue
    issues = data["issues"]
    assert all(i["code"] != "missing_mandatory" for i in issues)
    # Overall score should be reasonably high
    assert m["overall_score"] >= 0.6


def test_validate_xml_basic():
    xml = (
        """
        <akomaNtoso xmlns=\"http://docs.oasis-open.org/legaldocml/ns/akn/3.0\">
          <act>
            <body>
              <section eId=\"sec1\">
                <num>1</num>
                <heading>Section 1 Short title</heading>
                <content/>
              </section>
              <section eId=\"sec2\">
                <num>2</num>
                <heading>Section 2 Interpretation</heading>
                <content/>
              </section>
            </body>
          </act>
        </akomaNtoso>
        """
    )
    r = client.post("/api/v1/structure/validate/xml", json={"xml": xml})
    assert r.status_code == 200, r.text
    data = r.json()
    m = data["metrics"]
    for k, v in m.items():
        assert 0.0 <= v <= 1.0
    # Mandatory headings satisfied; no missing issues
    assert all(i["code"] != "missing_mandatory" for i in data["issues"])
