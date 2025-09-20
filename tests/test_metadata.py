# flake8: noqa
from fastapi.testclient import TestClient

from legal_os import create_app
from legal_os.settings import Settings


def test_metadata_extract_basic():
    app = create_app(Settings(env="test", debug=False, max_upload_mb=5))
    c = TestClient(app)
    data = b"%PDF-1.4\n..."
    files = {"file": ("doc.pdf", data, "application/pdf")}
    r = c.post("/metadata/extract", files=files)
    assert r.status_code == 200
    j = r.json()
    assert j["sha256"]
    assert j["extension"] == ".pdf"
    assert j["label"] == "pdf"
    assert 0.9 <= j["confidence"] <= 1.0
    assert j["issues"] == []


def test_metadata_extract_unsupported_and_large():
    app = create_app(Settings(env="test", debug=False, max_upload_mb=1))
    c = TestClient(app)
    data = b"0" * (2 * 1024 * 1024)
    files = {"file": ("bad.bin", data, "application/octet-stream")}
    r = c.post("/metadata/extract", files=files)
    assert r.status_code == 200
    j = r.json()
    assert "unsupported_type" in j["issues"]
    assert "too_large" in j["issues"]


