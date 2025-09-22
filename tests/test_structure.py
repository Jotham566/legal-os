import pytest
from fastapi.testclient import TestClient

from legal_os.main import app

client = TestClient(app)


def test_structure_parse_json_hierarchy_and_confidence():
    payload = {
        "content": [
            {"id": "part1", "heading": "Part I - General"},
            {"id": "chap1", "heading": "Chapter 1 — Preliminary"},
            {"id": "sec1", "heading": "Section 1 Short title"},
            {"id": "art2", "heading": "Article 2 Definitions"},
        ]
    }
    r = client.post("/api/v1/structure/parse/json", json=payload)
    assert r.status_code == 200, r.text
    data = r.json()
    nodes = data["nodes"]
    assert data["confidence"] == pytest.approx(1.0)

    assert nodes[0]["kind"] == "part" and nodes[0]["level"] == 1 and nodes[0]["parent_eid"] is None
    assert nodes[1]["kind"] == "chapter" and nodes[1]["level"] == 2 and nodes[1]["parent_eid"] == "part1"
    # Both section and article are level 3 and should parent to the chapter
    assert nodes[2]["kind"] == "section" and nodes[2]["level"] == 3 and nodes[2]["parent_eid"] == "chap1"
    assert nodes[3]["kind"] == "article" and nodes[3]["level"] == 3 and nodes[3]["parent_eid"] == "chap1"


def test_structure_parse_xml_sections_only():
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
    r = client.post("/api/v1/structure/parse/xml", json={"xml": xml})
    assert r.status_code == 200, r.text
    data = r.json()
    nodes = data["nodes"]
    assert len(nodes) == 2
    assert all(n["kind"] == "section" for n in nodes)
    # Because only sections are present, parser won't infer parents; parent_eid stays None
    assert all(n["parent_eid"] is None for n in nodes)
    assert data["confidence"] == pytest.approx(1.0)
