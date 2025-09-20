from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile

from ..services.compliance import LegalComplianceValidator, ComplianceReport

router = APIRouter(prefix="/compliance", tags=["compliance"])


@router.post("/validate", response_model=ComplianceReport)
async def validate(file: UploadFile = File(...)) -> ComplianceReport:
    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Empty file")
    validator = LegalComplianceValidator()
    return validator.validate_legal_structure(content, file.content_type)
