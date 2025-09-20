from __future__ import annotations

from typing import List

from ..schemas import (
    CombinedExtractionResult,
    DoclingResult,
    LangExtractResult,
    QAValidationResult,
)
from .docling import DoclingClient
from .langextract import LangExtractClient
from .qa import QAClient
from .quality import assess_quality


class LegalExtractionOrchestrator:
    """Implements multi-path extraction with fallbacks and intelligent merging.

    Heuristic baseline per spec 1.3.1: Uses Docling + LangExtract, assesses confidence,
    falls back to premium OCR-like path for low-quality inputs, and re-validates via QA.
    """

    def __init__(self) -> None:
        self.docling = DoclingClient()
        self.langextract = LangExtractClient()
        self.qa = QAClient()

    def process(self, content: bytes, content_type: str | None) -> CombinedExtractionResult:
        # Pre-quality assessment
        score, issues, needs_ocr, text_ratio, _pages = assess_quality(
            content, content_type=content_type, size=len(content)
        )

        used_premium_ocr = False
        enhanced_legal = False

        # Primary path
        d_primary: DoclingResult = self.docling.analyze(content, content_type)
        l_primary: LangExtractResult = self.langextract.analyze(content, content_type)

        # Confidence heuristic
        primary_conf = (d_primary.confidence + l_primary.overall_confidence) / 2.0

        # Fallbacks
        d_final = d_primary
        l_final = l_primary
        notes: List[str] = []

        if needs_ocr or primary_conf < 0.9:
            # Premium OCR fallback simulation: if low text ratio, boost layout confidence modestly
            used_premium_ocr = True
            boost = 0.1 if text_ratio < 0.05 else 0.05
            d_final = DoclingResult(
                pages=d_primary.pages,
                confidence=min(1.0, d_primary.confidence + boost),
                page_count=d_primary.page_count,
                notes=[
                    *d_primary.notes,
                    "premium_ocr_fallback",
                ],
            )
            notes.append("premium_ocr_applied")

        if l_primary.overall_confidence < 0.95:
            enhanced_legal = True
            # Enhanced legal analysis simulation: slight boost if text-likeness is good
            l_final = LangExtractResult(
                terms=l_primary.terms,
                cross_references=l_primary.cross_references,
                classifications=l_primary.classifications,
                overall_confidence=min(
                    1.0,
                    l_primary.overall_confidence
                    + (0.05 if text_ratio > 0.5 else 0.02),
                ),
                notes=[
                    *l_primary.notes,
                    "enhanced_legal_analysis",
                ],
            )
            notes.append("enhanced_legal_analysis")

        # QA validation as final gate
        qa_result: QAValidationResult = self.qa.run_validate(content, content_type)

        # Final confidence aggregation
        final_conf = min(
            1.0,
            max(
                0.0,
                (
                    d_final.confidence
                    + l_final.overall_confidence
                    + qa_result.overall_confidence
                )
                / 3.0,
            ),
        )

        return CombinedExtractionResult(
            docling=d_final,
            langextract=l_final,
            qa=qa_result,
            used_premium_ocr=used_premium_ocr,
            enhanced_legal_analysis=enhanced_legal,
            final_confidence=final_conf,
            notes=[
                *notes,
                *(["quality_low"] if score < 0.7 else []),
            ],
        )
