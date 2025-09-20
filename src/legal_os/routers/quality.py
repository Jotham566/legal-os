from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile

from ..services.quality import assess_quality

router = APIRouter(prefix="/quality", tags=["quality"])


@router.post("/validate")
async def validate_quality(file: UploadFile = File(...)) -> dict:
    content = await file.read()
    size = len(content)
    if size == 0:
        raise HTTPException(status_code=400, detail="Empty file")
    score, issues, needs_ocr, ratio, page_count = assess_quality(
        content, content_type=file.content_type, size=size
    )
    return {
        "score": score,
        "issues": issues,
        "needs_ocr": needs_ocr,
        "extractable_text_ratio": ratio,
        "page_count": page_count,
        "content_type": file.content_type,
        "size": size,
    }
