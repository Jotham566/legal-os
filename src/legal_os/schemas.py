from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class DocumentIn(BaseModel):
    title: Optional[str] = Field(default=None, max_length=512)


class DocumentOut(BaseModel):
    id: str
    created_at: datetime
    title: Optional[str] = None


class DocumentVersionIn(BaseModel):
    content: Dict[str, Any] = Field(default_factory=dict)


class DocumentVersionOut(BaseModel):
    id: str
    document_id: str
    version_number: int
    content: Dict[str, Any]
    created_at: datetime


class Grounding(BaseModel):
    page: Optional[int] = None
    x: Optional[float] = None
    y: Optional[float] = None
    width: Optional[float] = None
    height: Optional[float] = None


class Citation(BaseModel):
    text: str
    source_id: Optional[str] = None
    grounding: Optional[Grounding] = None


class ProcessingSessionCreate(BaseModel):
    source_key: Optional[str] = None
    total_steps: int = Field(ge=1, default=10)


class ProcessingSessionOut(BaseModel):
    id: str
    created_at: datetime
    updated_at: datetime
    status: str
    progress: int
    eta_seconds: Optional[int] = None
    checkpoints: Dict[str, Any]
    last_error: Optional[str] = None
    source_key: Optional[str] = None


class ProcessingSessionUpdate(BaseModel):
    status: Optional[str] = None
    progress: Optional[int] = Field(default=None, ge=0, le=100)
    eta_seconds: Optional[int] = Field(default=None, ge=0)
    checkpoint: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class QualityAssessmentOut(BaseModel):
    score: float = Field(ge=0.0, le=1.0)
    issues: list[str] = Field(default_factory=list)
    needs_ocr: bool = False
    extractable_text_ratio: float = Field(ge=0.0, le=1.0)
    page_count: Optional[int] = None
    content_type: Optional[str] = None
    size: int = 0


# Docling-like layout analysis schemas (simplified)
class LayoutBox(BaseModel):
    page: int = Field(ge=1)
    x: float = 0.0
    y: float = 0.0
    width: float = Field(ge=0.0, default=0.0)
    height: float = Field(ge=0.0, default=0.0)


class LayoutText(BaseModel):
    text: str
    confidence: float = Field(ge=0.0, le=1.0)
    box: LayoutBox


class LayoutBlock(BaseModel):
    kind: Literal["text", "table", "figure"] = "text"
    confidence: float = Field(ge=0.0, le=1.0)
    box: LayoutBox
    texts: List[LayoutText] = Field(default_factory=list)


class PageLayout(BaseModel):
    page_number: int = Field(ge=1)
    blocks: List[LayoutBlock] = Field(default_factory=list)


class DoclingResult(BaseModel):
    pages: List[PageLayout]
    confidence: float = Field(ge=0.0, le=1.0)
    page_count: int = Field(ge=0)
    notes: List[str] = Field(default_factory=list)


# LangExtract-like legal enhancement schemas (simplified)
class CharSpan(BaseModel):
    start: int = Field(ge=0)
    end: int = Field(ge=0)


class LegalTerm(BaseModel):
    text: str
    kind: Literal[
        "definition",
        "entity",
        "amount",
        "date",
        "rate",
        "section_heading",
    ] = "entity"
    span: CharSpan
    confidence: float = Field(ge=0.0, le=1.0)


class CrossReference(BaseModel):
    text: str
    source_span: CharSpan
    target_hint: Optional[str] = None
    confidence: float = Field(ge=0.0, le=1.0)


class LegalClassification(BaseModel):
    category: Literal[
        "penalty",
        "tax_rate",
        "amendment",
        "commencement",
        "jurisdiction",
        "other",
    ] = "other"
    span: CharSpan
    confidence: float = Field(ge=0.0, le=1.0)


class LangExtractResult(BaseModel):
    terms: List[LegalTerm] = Field(default_factory=list)
    cross_references: List[CrossReference] = Field(default_factory=list)
    classifications: List[LegalClassification] = Field(default_factory=list)
    overall_confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    notes: List[str] = Field(default_factory=list)


# GPT QA validation schemas (simplified)
class QAValidationMetrics(BaseModel):
    structure_valid: bool
    reasoning_ok: bool
    cross_references_ok: bool
    compliance_ok: bool
    structure_confidence: float = Field(ge=0.0, le=1.0)
    reasoning_confidence: float = Field(ge=0.0, le=1.0)
    cross_references_confidence: float = Field(ge=0.0, le=1.0)
    compliance_confidence: float = Field(ge=0.0, le=1.0)


class QAValidationResult(BaseModel):
    model_used: Literal["gpt-5", "gpt-5-mini"]
    corrections_applied: int = Field(ge=0)
    issues: List[str] = Field(default_factory=list)
    metrics: QAValidationMetrics
    overall_confidence: float = Field(ge=0.0, le=1.0)
    notes: List[str] = Field(default_factory=list)


class CombinedExtractionResult(BaseModel):
    docling: DoclingResult
    langextract: LangExtractResult
    qa: QAValidationResult
    used_premium_ocr: bool = False
    enhanced_legal_analysis: bool = False
    final_confidence: float = Field(ge=0.0, le=1.0)
    notes: List[str] = Field(default_factory=list)


class ReviewTaskOut(BaseModel):
    id: str
    status: Literal["queued", "in_review", "completed", "rejected"]
    priority: Literal["low", "medium", "high", "critical"]
    expert_type: Literal[
        "constitutional_law_expert",
        "tax_law_expert",
        "commercial_law_expert",
        "general_legal_expert",
    ]
    reasons: List[str] = Field(default_factory=list)
    final_confidence: float = Field(ge=0.0, le=1.0)
    created_at: datetime
    updated_at: datetime
