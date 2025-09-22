from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from ..settings import Settings, get_settings
from ..storage import (
    get_storage_from_settings,
    document_original_key,
    artifact_key,
)
from ..dependencies import require_any_role
from ..audit import log_event
from ..db import session_scope

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])


class PresignResponse(BaseModel):
    url: str


@router.get("/{document_id}/versions/{version_id}/download", response_model=PresignResponse)
async def get_original_download_url(
    request: Request,
    document_id: str,
    version_id: str,
    settings: Settings = Depends(get_settings),
    _user: dict = Depends(require_any_role("viewer", "editor", "admin")),
) -> PresignResponse:
    # Cap overly long expiries for safety (e.g., 1 hour)
    if settings.minio_url_expires_seconds > 3600:
        raise HTTPException(status_code=400, detail="Expiry too long; max 3600 seconds")

    st = get_storage_from_settings(settings)
    key = document_original_key(document_id, version_id)
    url = st.url_for(key)
    if not url:
        # Avoid existence leakage; generic 404
        raise HTTPException(status_code=404, detail="URL not available")

    # Audit presign issuance
    with session_scope() as s:
        log_event(
            s,
            actor=_user.get("username", "unknown"),
            action="presign_issued",
            entity_type="document",
            entity_id=f"{document_id}:{version_id}",
            meta={
                "path": str(request.url.path),
                "key": key,
                "expiry_seconds": settings.minio_url_expires_seconds,
                "artifact": None,
            },
        )
    return PresignResponse(url=url)


@router.get(
    "/{document_id}/versions/{version_id}/artifacts/{name}",
    response_model=PresignResponse,
)
async def get_artifact_download_url(
    request: Request,
    document_id: str,
    version_id: str,
    name: str,
    settings: Settings = Depends(get_settings),
    _user: dict = Depends(require_any_role("viewer", "editor", "admin")),
) -> PresignResponse:
    if settings.minio_url_expires_seconds > 3600:
        raise HTTPException(status_code=400, detail="Expiry too long; max 3600 seconds")

    st = get_storage_from_settings(settings)
    key = artifact_key(document_id, version_id, name)
    url = st.url_for(key)
    if not url:
        raise HTTPException(status_code=404, detail="URL not available")

    # Audit presign issuance
    with session_scope() as s:
        log_event(
            s,
            actor=_user.get("username", "unknown"),
            action="presign_issued",
            entity_type="document_artifact",
            entity_id=f"{document_id}:{version_id}:{name}",
            meta={
                "path": str(request.url.path),
                "key": key,
                "expiry_seconds": settings.minio_url_expires_seconds,
                "artifact": name,
            },
        )
    return PresignResponse(url=url)
