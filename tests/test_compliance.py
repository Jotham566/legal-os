from __future__ import annotations

import io

from fastapi.testclient import TestClient

from legal_os.main import create_app


def make_client():
    app = create_app()
    return TestClient(app)


def test_compliance_empty_rejected():
    client = make_client()
    files = {"file": ("doc.pdf", io.BytesIO(b""), "application/pdf")}
    res = client.post("/compliance/validate", files=files)
    assert res.status_code == 400


def test_compliance_returns_scores_and_flags():
    client = make_client()
    text = (
        "1. Short title and commencement\n"
        "2. Definitions\n"
        "In this Act, \"tax\" means a levy...\n"
        "Part I\n"
        "Refer to Section 2\n"
        "This Act is amended...\n"
    ).encode()
    files = {"file": ("doc.pdf", io.BytesIO(text), "application/pdf")}
    res = client.post("/compliance/validate", files=files)
    assert res.status_code == 200
    payload = res.json()
    checks = payload["checks"]
    # Ensure each check is within [0,1]
    for k, v in checks.items():
        assert 0.0 <= v <= 1.0
    assert 0.0 <= payload["overall_compliance"] <= 1.0
    # Heuristics should detect numbering, definitions, cross refs
    assert payload["overall_compliance"] > 0.5
