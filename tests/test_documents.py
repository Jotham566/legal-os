from __future__ import annotations

from fastapi.testclient import TestClient

from legal_os import create_app
from legal_os.settings import Settings, FeatureFlags
from legal_os.dependencies import _RATE_BUCKET


def client(settings: Settings | None = None) -> TestClient:
    app = create_app(settings or Settings(env="test", debug=False))
    return TestClient(app)


def _token(c: TestClient, username: str = "admin", password: str = "admin") -> str:
    # Reset rate limiter to avoid cross-test flakiness
    _RATE_BUCKET.clear()
    res = c.post(
        "/auth/token",
        data={"username": username, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert res.status_code == 200
    return res.json()["access_token"]


def test_presign_endpoints_return_404_when_local_storage():
    c = client(Settings(env="test", debug=False, flags=FeatureFlags(enable_minio=False)))
    token = _token(c)  # admin role
    r1 = c.get(
        "/api/v1/documents/doc1/versions/v1/download",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r1.status_code == 404
    r2 = c.get(
        "/api/v1/documents/doc1/versions/v1/artifacts/preview.png",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r2.status_code == 404
