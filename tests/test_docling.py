from __future__ import annotations

from fastapi.testclient import TestClient

from legal_os import create_app


def client():
    return TestClient(create_app())


def test_docling_rejects_empty():
    c = client()
    files = {"file": ("empty.pdf", b"", "application/pdf")}
    r = c.post("/docling/analyze", files=files)
    assert r.status_code == 400


def test_docling_text_confidence_higher():
    c = client()
    content_text = b"%PDF-1.4\nSome text content within the pdf"
    files = {"file": ("doc.pdf", content_text, "application/pdf")}
    r = c.post("/docling/analyze", files=files)
    assert r.status_code == 200, r.text
    data_text = r.json()

    content_bin = bytes([0] * 1000)
    files = {"file": ("img.pdf", content_bin, "application/pdf")}
    r2 = c.post("/docling/analyze", files=files)
    assert r2.status_code == 200
    data_bin = r2.json()

    assert data_text["confidence"] >= data_bin["confidence"]
    assert data_text["pages"][0]["blocks"][0]["kind"] in ("text",)
    assert data_bin["pages"][0]["blocks"][0]["kind"] in ("figure", "text")


def test_docling_confidence_bounds():
    c = client()
    content = b"random text"
    files = {"file": ("doc.pdf", content, "application/pdf")}
    r = c.post("/docling/analyze", files=files)
    assert r.status_code == 200
    data = r.json()
    assert 0.0 <= data["confidence"] <= 1.0
