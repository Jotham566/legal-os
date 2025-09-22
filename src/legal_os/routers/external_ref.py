from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from ..services.external_ref import ExternalRefResolver

router = APIRouter(prefix="/api/v1/structure/external", tags=["external-refs"])


class ResolveJsonIn(BaseModel):
    content: list[dict]


class ResolveXmlIn(BaseModel):
    xml: str


class RefOut(BaseModel):
    text: str
    kind: str
    authority: str
    jurisdiction: str
    canonical_uri: str | None
    confidence: float


class MetricsOut(BaseModel):
    total: int
    resolved: int
    resolution_rate: float


class ResolveOut(BaseModel):
    refs: list[RefOut]
    metrics: MetricsOut
    issues: list[str]


@router.post("/resolve/json", response_model=ResolveOut)
async def resolve_json(payload: ResolveJsonIn) -> ResolveOut:
    r = ExternalRefResolver().resolve_from_json(payload.content)
    return ResolveOut(
        refs=[RefOut(**ref.__dict__) for ref in r.refs],
        metrics=MetricsOut(**r.metrics.__dict__),
        issues=r.issues,
    )


@router.post("/resolve/xml", response_model=ResolveOut)
async def resolve_xml(payload: ResolveXmlIn) -> ResolveOut:
    r = ExternalRefResolver().resolve_from_akn_xml(payload.xml)
    return ResolveOut(
        refs=[RefOut(**ref.__dict__) for ref in r.refs],
        metrics=MetricsOut(**r.metrics.__dict__),
        issues=r.issues,
    )
