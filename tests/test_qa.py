from __future__ import annotations

from fastapi.testclient import TestClient

from legal_os import create_app


def client():
    return TestClient(create_app())


def test_qa_rejects_empty():
    c = client()
    r = c.post("/qa/validate", files={"file": ("empty.txt", b"", "text/plain")})
    assert r.status_code == 400


def test_qa_returns_metrics_and_model_selection():
    c = client()
    text = (
        "Section 1. Short title and commencement.\n"
        "Refer to Section 3 for penalties and amendment details.\n"
        "The rate is 5% effective on 1 July 2024."
    )
    r = c.post("/qa/validate", files={"file": ("doc.txt", text.encode("utf-8"), "text/plain")})
    assert r.status_code == 200, r.text
    data = r.json()

    assert data["model_used"] in ("gpt-5", "gpt-5-mini")
    assert 0.0 <= data["overall_confidence"] <= 1.0

    m = data["metrics"]
    assert set(m.keys()) == {
        "structure_valid",
        "reasoning_ok",
        "cross_references_ok",
        "compliance_ok",
        "structure_confidence",
        "reasoning_confidence",
        "cross_references_confidence",
        "compliance_confidence",
    }


def test_qa_model_selection_switches_on_size():
    c = client()
    # Large input favors full model
    big_text = ("Section X\n" + ("A" * 6000)).encode("utf-8")
    r = c.post("/qa/validate", files={"file": ("big.txt", big_text, "text/plain")})
    assert r.status_code == 200
    model = r.json()["model_used"]
    assert model == "gpt-5"
