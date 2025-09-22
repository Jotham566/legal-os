from __future__ import annotations

from typing import Annotated
from fastapi import APIRouter, UploadFile, File, HTTPException

from ..services.recovery import LegalErrorRecoverySystem, RecoveryReport

router = APIRouter(prefix="/error-recovery", tags=["error-recovery"])


@router.post("/attempt", response_model=RecoveryReport)
async def attempt_recovery(file: Annotated[UploadFile, File(...)]) -> RecoveryReport:
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")
    system = LegalErrorRecoverySystem()
    report = system.recover(data)
    return report
