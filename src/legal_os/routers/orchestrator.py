from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile

from ..schemas import CombinedExtractionResult
from ..services.orchestrator import LegalExtractionOrchestrator

router = APIRouter(prefix="/extract", tags=["orchestrator"])


@router.post("/process", response_model=CombinedExtractionResult)
async def process(file: UploadFile = File(...)) -> CombinedExtractionResult:
    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Empty file")
    orch = LegalExtractionOrchestrator()
    return orch.process(content, file.content_type)
