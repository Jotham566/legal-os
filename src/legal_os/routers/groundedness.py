from __future__ import annotations

from fastapi import APIRouter, Body

from ..services.groundedness import GroundednessReport, GroundednessValidator

router = APIRouter(prefix="/groundedness", tags=["groundedness"])


@router.post("/verify", response_model=GroundednessReport)
async def verify(
    extracted_text: str = Body(..., embed=True),
    source_text: str = Body(..., embed=True),
) -> GroundednessReport:
    validator = GroundednessValidator()
    return validator.verify(extracted_text, source_text)
