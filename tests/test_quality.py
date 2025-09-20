from __future__ import annotations

from fastapi.testclient import TestClient

from legal_os import create_app


def client():
    return TestClient(create_app())


def test_quality_rejects_empty():
    c = client()
    files = {"file": ("empty.pdf", b"", "application/pdf")}
    r = c.post("/quality/validate", files=files)
    assert r.status_code == 400


def test_quality_pdf_with_text():
    c = client()
    content = b"%PDF-1.4\nHello world text inside"
    files = {"file": ("doc.pdf", content, "application/pdf")}
    r = c.post("/quality/validate", files=files)
    assert r.status_code == 200, r.text
    data = r.json()
    assert 0.0 <= data["score"] <= 1.0
    assert data["content_type"] == "application/pdf"
    assert data["size"] == len(content)
    assert 0.0 <= data["extractable_text_ratio"] <= 1.0


def test_quality_flags_ocr_for_binary_pdf():
    c = client()
    # Mostly non-text bytes simulate scanned image
    content = bytes([0] * 10000)
    files = {"file": ("scan.pdf", content, "application/pdf")}
    r = c.post("/quality/validate", files=files)
    assert r.status_code == 200
    data = r.json()
    assert data["needs_ocr"] is True


def test_quality_unsupported_type():
    c = client()
    content = b"hello"
    files = {"file": ("doc.bin", content, "application/octet-stream")}
    r = c.post("/quality/validate", files=files)
    assert r.status_code == 200
    data = r.json()
    assert "Unsupported content type" in data["issues"]
