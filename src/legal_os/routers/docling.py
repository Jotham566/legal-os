from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile

from ..services.docling import DoclingClient
from ..schemas import DoclingResult

router = APIRouter(prefix="/docling", tags=["docling"])


@router.post("/analyze", response_model=DoclingResult)
async def analyze(file: UploadFile = File(...)) -> DoclingResult:
    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Empty file")
    client = DoclingClient()
    result = client.analyze(content, file.content_type)
    return result
