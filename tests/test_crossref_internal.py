from fastapi.testclient import TestClient

from legal_os.main import app

client = TestClient(app)


def test_crossref_resolve_json():
    content = [
        {"id": "s1", "heading": "Section 1 Short title", "text": "See section 2 and Article 3."},
        {"id": "s2", "heading": "Section 2 Interpretation", "text": "As defined in section 1."},
        {"id": "a3", "heading": "Article 3 Scope", "text": "This is standalone."},
    ]
    r = client.post("/api/v1/structure/crossref/resolve/json", json={"content": content})
    assert r.status_code == 200, r.text
    data = r.json()
    edges = data["edges"]
    # Expect at least references to section 2 and article 3
    targets = {(e["target_kind"], e["target_number"]) for e in edges}
    assert ("section", "2") in targets
    assert ("article", "3") in targets
    # Resolution rate should be >= 0.66 since two of three should resolve
    assert data["metrics"]["resolution_rate"] >= 0.66


def test_crossref_resolve_xml():
    xml = (
        """
        <akomaNtoso xmlns=\"http://docs.oasis-open.org/legaldocml/ns/akn/3.0\">
          <act>
            <body>
              <section eId=\"s1\"><num>1</num><heading>Section 1 Short title</heading><content>See section 2.</content></section>
              <section eId=\"s2\"><num>2</num><heading>Section 2 Interpretation</heading><content>As defined in section 1.</content></section>
              <article eId=\"a3\"><num>3</num><heading>Article 3 Scope</heading><content>Standalone.</content></article>
            </body>
          </act>
        </akomaNtoso>
        """
    )
    r = client.post("/api/v1/structure/crossref/resolve/xml", json={"xml": xml})
    assert r.status_code == 200, r.text
    data = r.json()
    edges = data["edges"]
    # Two edges referencing 2 and 1 respectively
    targets = {(e["target_kind"], e["target_number"]) for e in edges}
    assert ("section", "2") in targets
    assert ("section", "1") in targets
    assert data["metrics"]["total_refs"] >= 2
