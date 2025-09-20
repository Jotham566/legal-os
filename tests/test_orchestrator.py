from __future__ import annotations

import io

from fastapi.testclient import TestClient

from legal_os.main import create_app


def make_client():
    app = create_app()
    return TestClient(app)


def test_orchestrator_process_happy_path_pdf_texty():
    client = make_client()
    # Simulate a text-rich PDF by sending ASCII bytes and content-type
    data = b"Section 1. Short title and commencement. Penalty 5%. See Section 2. Uganda"
    files = {"file": ("doc.pdf", io.BytesIO(data), "application/pdf")}
    res = client.post("/extract/process", files=files)
    assert res.status_code == 200
    payload = res.json()
    assert payload["docling"]["confidence"] >= 0.5
    assert payload["langextract"]["overall_confidence"] >= 0.5
    assert 0.0 <= payload["final_confidence"] <= 1.0
    assert payload["used_premium_ocr"] in (True, False)
    assert payload["enhanced_legal_analysis"] in (True, False)


def test_orchestrator_process_empty_rejected():
    client = make_client()
    files = {"file": ("doc.pdf", io.BytesIO(b""), "application/pdf")}
    res = client.post("/extract/process", files=files)
    assert res.status_code == 400


def test_orchestrator_process_low_quality_triggers_fallbacks():
    client = make_client()
    # Simulate low text ratio to trigger OCR fallback
    data = bytes([0, 1, 2, 3, 4, 5]) * 2000
    files = {"file": ("scan.pdf", io.BytesIO(data), "application/pdf")}
    res = client.post("/extract/process", files=files)
    assert res.status_code == 200
    payload = res.json()
    # When low text ratio, we expect premium OCR fallback to be applied
    assert payload["used_premium_ocr"] is True
    # Legal analysis may still be low confidence -> enhanced path flagged
    assert payload["enhanced_legal_analysis"] in (True, False)
