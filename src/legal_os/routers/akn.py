from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..services.akn import transform_to_akn, validate_akn_xml, AKNError

router = APIRouter(prefix="/api/v1/akn", tags=["akn"])


class AKNTransformIn(BaseModel):
    metadata: dict | None = None
    content: list[dict] | None = None


class AKNTransformOut(BaseModel):
    xml: str


@router.post("/transform", response_model=AKNTransformOut)
async def akn_transform(payload: AKNTransformIn) -> AKNTransformOut:
    doc = {"metadata": payload.metadata or {}, "content": payload.content or []}
    try:
        xml_bytes = transform_to_akn(doc)
        validate_akn_xml(xml_bytes)
    except AKNError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return AKNTransformOut(xml=xml_bytes.decode("utf-8"))
