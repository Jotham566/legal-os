from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile

from ..services.langextract import LangExtractClient
from ..schemas import LangExtractResult

router = APIRouter(prefix="/langextract", tags=["langextract"])


@router.post("/analyze", response_model=LangExtractResult)
async def analyze(file: UploadFile = File(...)) -> LangExtractResult:
    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Empty file")
    client = LangExtractClient()
    result = client.analyze(content, file.content_type)
    return result
