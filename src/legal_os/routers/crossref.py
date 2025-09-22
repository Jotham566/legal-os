from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from ..services.crossref import CrossRefResolver

router = APIRouter(prefix="/api/v1/structure/crossref", tags=["crossref"])


class ResolveJsonIn(BaseModel):
    content: list[dict]


class ResolveXmlIn(BaseModel):
    xml: str


class EdgeOut(BaseModel):
    source_eid: str
    ref_text: str
    target_kind: str
    target_number: str
    target_eid: str | None
    confidence: float


class MetricsOut(BaseModel):
    total_refs: int
    resolved_refs: int
    resolution_rate: float


class ResolveOut(BaseModel):
    edges: list[EdgeOut]
    issues: list[str]
    metrics: MetricsOut


@router.post("/resolve/json", response_model=ResolveOut)
async def resolve_json(payload: ResolveJsonIn) -> ResolveOut:
    r = CrossRefResolver().resolve_from_json(payload.content)
    return ResolveOut(
        edges=[EdgeOut(**e.__dict__) for e in r.edges],
        issues=r.issues,
        metrics=MetricsOut(**r.metrics.__dict__),
    )


@router.post("/resolve/xml", response_model=ResolveOut)
async def resolve_xml(payload: ResolveXmlIn) -> ResolveOut:
    r = CrossRefResolver().resolve_from_akn_xml(payload.xml)
    return ResolveOut(
        edges=[EdgeOut(**e.__dict__) for e in r.edges],
        issues=r.issues,
        metrics=MetricsOut(**r.metrics.__dict__),
    )
