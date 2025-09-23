from fastapi.testclient import TestClient

from legal_os.main import app

client = TestClient(app)


def test_embed_json_pipeline_shapes_and_norm():
    content = [
        {"text": "Section 1 Short title."},
        {"text": "Section 2 Interpretation and application."},
    ]
    r = client.post(
        "/api/v1/embeddings/json",
        json={
            "content": content,
            "model": "text-embedding-3-large",
            "dim": 64,
            "max_chars_per_chunk": 50,
            "overlap": 10,
        },
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["model"] == "text-embedding-3-large"
    assert data["dim"] == 64
    assert data["chunks"], "no chunks produced"
    # vectors are unit-norm (approximately)
    def l2(vec):
        return sum(v * v for v in vec) ** 0.5

    for c in data["chunks"]:
        assert len(c["vector"]) == 64
        n = l2(c["vector"])
        assert 0.99 <= n <= 1.01


def test_embed_xml_pipeline_basic():
    xml = (
        """
        <akomaNtoso xmlns=\"http://docs.oasis-open.org/legaldocml/ns/akn/3.0\">
          <act>
            <body>
              <section eId=\"s1\"><num>1</num><heading>Section 1 Short title</heading><content>Text A.</content></section>
              <section eId=\"s2\"><num>2</num><heading>Section 2 Interpretation</heading><content>Text B.</content></section>
            </body>
          </act>
        </akomaNtoso>
        """
    )
    r = client.post(
        "/api/v1/embeddings/xml",
        json={"xml": xml, "model": "text-embedding-3-large", "dim": 16, "max_chars_per_chunk": 20, "overlap": 5},
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["dim"] == 16
    assert data["chunks"]
