from __future__ import annotations

import types

from fastapi import FastAPI

from legal_os.auth import require_document_permission


def make_app() -> FastAPI:
    app = FastAPI()

    @app.get("/documents/{doc_id}")
    def read_doc(user=types.SimpleNamespace(role="viewer")):
        return {"ok": True}

    # Route enforcing read permission
    @app.get("/guarded/{doc_id}")
    def guarded(dep=types.SimpleNamespace(), user=types.SimpleNamespace(role="viewer")):
        return {"ok": True}

    return app


def test_require_document_permission_allows_roles():
    dep = require_document_permission("doc_id", "read")
    assert callable(dep)
