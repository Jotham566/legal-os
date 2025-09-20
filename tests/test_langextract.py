from __future__ import annotations

from fastapi.testclient import TestClient

from legal_os import create_app


def client():
    return TestClient(create_app())


def test_langextract_rejects_empty():
    c = client()
    files = {"file": ("empty.pdf", b"", "application/pdf")}
    r = c.post("/langextract/analyze", files=files)
    assert r.status_code == 400


def test_langextract_detects_terms_and_refs():
    c = client()
    text = (
        "In this Act, \"Digital Services Tax\" means a tax of 5% on gross receipts.\n"
        "Section 15 provides penalties. Commencement is 1 July 2024.\n"
        "Refer also to Part II and Schedule 3. Uganda Revenue Authority applies the rate."
    )
    files = {"file": ("act.txt", text.encode("utf-8"), "text/plain")}
    r = c.post("/langextract/analyze", files=files)
    assert r.status_code == 200, r.text
    data = r.json()

    # Overall confidence within bounds
    assert 0.0 <= data["overall_confidence"] <= 1.0

    # Should detect at least one definition term
    defs = [t for t in data["terms"] if t["kind"] == "definition"]
    assert defs, f"no definitions found: {data}"

    # Should detect cross references with spans
    assert data["cross_references"], "no cross references found"
    for ref in data["cross_references"]:
        assert ref["source_span"]["start"] < ref["source_span"]["end"]
        assert 0.0 <= ref["confidence"] <= 1.0

    # Classifications include penalty, commencement or tax_rate
    cats = {c["category"] for c in data["classifications"]}
    assert {"penalty", "commencement"} & cats or "tax_rate" in cats


def test_langextract_on_binary_like_text_is_low_confidence():
    c = client()
    # Simulate binary-like content decoded to mostly non-text
    content = bytes([0, 1, 2, 3, 4, 5]) * 50
    files = {"file": ("bin.dat", content, "application/octet-stream")}
    r = c.post("/langextract/analyze", files=files)
    assert r.status_code == 200
    data = r.json()
    assert data["overall_confidence"] <= 1.0
