from __future__ import annotations

import json
from fastapi.testclient import TestClient

from legal_os.main import create_app


def test_request_logging_includes_request_id(monkeypatch, capsys):
    # Capture stdout logs
    app = create_app()
    client = TestClient(app)
    res = client.get("/health", headers={"X-Request-ID": "rid-123"})
    assert res.status_code == 200
    # Flush and read captured stdout
    captured = capsys.readouterr().out.strip().splitlines()
    # Should have at least one JSON log line from our middleware
    assert any(json.loads(line).get("request_id") == "rid-123" for line in captured)
