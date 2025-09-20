from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile

from ..settings import Settings, get_settings
from ..services.metadata import extract_metadata, is_duplicate, validate_metadata

router = APIRouter(prefix="/metadata", tags=["metadata"])


@router.post("/extract")
async def metadata_extract(
    file: Annotated[UploadFile, File(...)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict[str, object]:
    data = await file.read()
    meta = extract_metadata(file.filename or "", file.content_type or "", data)
    issues = validate_metadata(meta, settings)
    duplicate = is_duplicate(meta.sha256)  # Caller may provide known_hashes later
    return {
        "filename": meta.filename,
        "content_type": meta.content_type,
        "size": meta.size,
        "sha256": meta.sha256,
        "extension": meta.extension,
        "title_guess": meta.title_guess,
        "label": meta.label,
        "confidence": meta.confidence,
        "issues": issues,
        "duplicate": duplicate,
    }
