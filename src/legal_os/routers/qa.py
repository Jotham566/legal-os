from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile

from ..schemas import QAValidationResult
from ..services.qa import QAClient


router = APIRouter(prefix="/qa", tags=["qa"])


@router.post("/validate", response_model=QAValidationResult)
async def validate(file: UploadFile = File(...)) -> QAValidationResult:
    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Empty file")
    client = QAClient()
    return client.run_validate(content, file.content_type)
