from __future__ import annotations

import hashlib
import io
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from ..settings import Settings, get_settings
from ..storage import get_storage_from_settings

router = APIRouter(prefix="/upload", tags=["upload"])

ALLOWED_TYPES = {
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "application/vnd.oasis.opendocument.text": ".odt",
}


def _scan_for_virus(data: bytes) -> bool:
    # Placeholder: return False when clean, True when virus detected
    # In future integrate ClamAV or a SaaS scanning API
    return False


@router.post("", status_code=201)
async def upload_file(
    file: Annotated[UploadFile, File(...)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict[str, object]:

    # Validate content type
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=415, detail="Unsupported file type")

    # Read into memory up to max allowed; stream to storage afterwards
    max_bytes = settings.max_upload_mb * 1024 * 1024
    data = await file.read()
    if len(data) == 0:
        raise HTTPException(status_code=400, detail="Empty file")
    if len(data) > max_bytes:
        raise HTTPException(status_code=413, detail="File too large")

    # Virus scan placeholder
    if _scan_for_virus(data):
        raise HTTPException(status_code=400, detail="File failed virus scan")

    # Compute checksum and store
    sha256 = hashlib.sha256(data).hexdigest()
    ext = ALLOWED_TYPES[file.content_type]
    key = f"documents/{sha256}{ext}"

    st = get_storage_from_settings(settings)
    stream = io.BytesIO(data)
    st.put_object(key, stream, len(data))

    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "sha256": sha256,
        "size": len(data),
        "storage_key": key,
        "url": st.url_for(key),
    }
