from __future__ import annotations

from fastapi.testclient import TestClient
from legal_os.dependencies import _RATE_BUCKET

from legal_os.main import create_app


def _client():
    app = create_app()
    return TestClient(app)


def test_token_issuance_and_protected_route():
    client = _client()
    # Valid login
    res = client.post(
        "/auth/token",
        data={"username": "admin", "password": "admin"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert res.status_code == 200
    token = res.json()["access_token"]

    # Access protected admin route
    res2 = client.get("/admin", headers={"Authorization": f"Bearer {token}"})
    assert res2.status_code == 200
    j = res2.json()
    assert j["role"] == "admin"


def test_invalid_login_rejected():
    client = _client()
    res = client.post(
        "/auth/token",
        data={"username": "user", "password": "wrong"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert res.status_code == 401


def test_rbac_forbidden_for_non_admin():
    client = _client()
    # Regular user can get token
    res = client.post(
        "/auth/token",
        data={"username": "user", "password": "user"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert res.status_code == 200
    token = res.json()["access_token"]

    # But cannot access admin route
    res2 = client.get("/admin", headers={"Authorization": f"Bearer {token}"})
    assert res2.status_code == 403


def test_security_headers_present():
    client = _client()
    res = client.get("/health")
    assert res.headers.get("X-Content-Type-Options") == "nosniff"
    assert res.headers.get("X-Frame-Options") == "DENY"
    assert "default-src" in res.headers.get("Content-Security-Policy", "")


def test_rate_limiting_on_token_endpoint():
    client = _client()
    # Reset limiter state for deterministic behavior
    _RATE_BUCKET.clear()
    # Exceed 5 requests quickly
    for _ in range(5):
        client.post(
            "/auth/token",
            data={"username": "user", "password": "wrong"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
    res = client.post(
        "/auth/token",
        data={"username": "user", "password": "wrong"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert res.status_code == 429
