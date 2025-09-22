from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from ..services.structure import StructureParser
from ..services.structure_validation import LegalStructureValidator

router = APIRouter(prefix="/api/v1/structure", tags=["structure"])


class ParseJsonIn(BaseModel):
    content: list[dict]


class ParseXmlIn(BaseModel):
    xml: str


class NodeOut(BaseModel):
    eid: str
    heading: str
    kind: str
    number: str | None
    level: int
    parent_eid: str | None


class ParseOut(BaseModel):
    nodes: list[NodeOut]
    confidence: float


class ValidationMetricsOut(BaseModel):
    pattern_recognition: float
    numbering_consistency: float
    mandatory_sections: float
    amendment_tracking: float
    overall_score: float


class ValidationIssueOut(BaseModel):
    code: str
    message: str
    severity: str
    eid: str | None = None


class ValidationOut(BaseModel):
    metrics: ValidationMetricsOut
    issues: list[ValidationIssueOut]


@router.post("/parse/json", response_model=ParseOut)
async def parse_json(payload: ParseJsonIn) -> ParseOut:
    parser = StructureParser()
    res = parser.parse_from_json(payload.content)
    return ParseOut(
        nodes=[NodeOut(**n.__dict__) for n in res.nodes],
        confidence=res.confidence,
    )


@router.post("/parse/xml", response_model=ParseOut)
async def parse_xml(payload: ParseXmlIn) -> ParseOut:
    parser = StructureParser()
    res = parser.parse_from_akn_xml(payload.xml)
    return ParseOut(
        nodes=[NodeOut(**n.__dict__) for n in res.nodes],
        confidence=res.confidence,
    )


@router.post("/validate/json", response_model=ValidationOut)
async def validate_json(payload: ParseJsonIn) -> ValidationOut:
    validator = LegalStructureValidator()
    res = validator.validate_from_json(payload.content)
    return ValidationOut(
        metrics=ValidationMetricsOut(**res.metrics.__dict__),
        issues=[ValidationIssueOut(**i.__dict__) for i in res.issues],
    )


@router.post("/validate/xml", response_model=ValidationOut)
async def validate_xml(payload: ParseXmlIn) -> ValidationOut:
    validator = LegalStructureValidator()
    res = validator.validate_from_akn_xml(payload.xml)
    return ValidationOut(
        metrics=ValidationMetricsOut(**res.metrics.__dict__),
        issues=[ValidationIssueOut(**i.__dict__) for i in res.issues],
    )
