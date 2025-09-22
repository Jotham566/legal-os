from __future__ import annotations

from fastapi.testclient import TestClient

from legal_os import create_app
from legal_os.settings import Settings, FeatureFlags


class DummyStorage:
    def __init__(self, url: str):
        self._url = url

    def put_object(self, key, stream, length):  # pragma: no cover - not used here
        pass

    def url_for(self, key: str) -> str | None:
        return f"{self._url}/{key}"


def test_presign_endpoints_with_mocked_minio(monkeypatch):
    settings = Settings(
        env="test",
        debug=False,
        flags=FeatureFlags(enable_minio=True),
        minio_endpoint="localhost:9000",
        minio_access_key="x",
        minio_secret_key="y",
        minio_bucket="docs",
        minio_secure=False,
    )
    # Monkeypatch get_storage_from_settings to return DummyStorage
    from legal_os import main as main_mod

    def fake_get_storage_from_settings(s):
        return DummyStorage("https://example.com")

    app = create_app(settings)
    # Override dependency by monkeypatching module reference where used
    monkeypatch.setattr(
        main_mod.documents_router,  # router module imported in main
        "get_settings",
        lambda: settings,
        raising=False,
    )
    c = TestClient(app)

    # Obtain admin token for Authorization header
    res = c.post(
        "/auth/token",
        data={"username": "admin", "password": "admin"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert res.status_code == 200
    token = res.json()["access_token"]

    # Patch storage accessor in router module directly
    import legal_os.routers.documents as docs_router

    monkeypatch.setattr(
        docs_router, "get_storage_from_settings", fake_get_storage_from_settings
    )

    r1 = c.get(
        "/api/v1/documents/doc1/versions/v1/download",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r1.status_code == 200
    assert r1.json()["url"].startswith("https://example.com/")

    r2 = c.get(
        "/api/v1/documents/doc1/versions/v1/artifacts/preview.png",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r2.status_code == 200
    assert r2.json()["url"].startswith("https://example.com/")
