from fastapi.testclient import TestClient

from legal_os import create_app
from legal_os.settings import Settings


def client():
    app = create_app(Settings(env="test", debug=False))
    return TestClient(app)


def test_upload_pdf_success(tmp_path):
    c = client()
    content = b"%PDF-1.4 minimal pdf bytes"
    files = {"file": ("test.pdf", content, "application/pdf")}
    r = c.post("/upload", files=files)
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["content_type"] == "application/pdf"
    assert data["size"] == len(content)
    assert data["sha256"]
    assert data["storage_key"].endswith(".pdf")


def test_reject_large_file(monkeypatch):
    c = client()
    # Force smaller limit
    monkeypatch.setenv("MAX_UPLOAD_MB", "1")
    app = create_app(Settings(env="test", debug=False, max_upload_mb=1))
    c = TestClient(app)

    content = b"0" * (2 * 1024 * 1024)
    files = {"file": ("big.pdf", content, "application/pdf")}
    r = c.post("/upload", files=files)
    assert r.status_code == 413


essential_types = [
    ("text/plain", "Unsupported file type"),
    ("application/zip", "Unsupported file type"),
]


def test_reject_unsupported_type():
    c = client()
    content = b"hello"
    files = {"file": ("test.txt", content, "text/plain")}
    r = c.post("/upload", files=files)
    assert r.status_code == 415


def test_empty_file_rejected():
    c = client()
    files = {"file": ("empty.pdf", b"", "application/pdf")}
    r = c.post("/upload", files=files)
    assert r.status_code == 400
