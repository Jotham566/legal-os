from __future__ import annotations

from typing import List, Optional
from dataclasses import dataclass
from pydantic import BaseModel
import re


class FailureAnalysis(BaseModel):
    failure_causes: List[str]
    notes: Optional[str] = None


class RecoveryStepResult(BaseModel):
    step: str
    applied: bool
    detail: Optional[str] = None


class RecoveryReport(BaseModel):
    recovered: bool
    requires_manual: bool
    applied_strategies: List[RecoveryStepResult]
    confidence_before: float
    confidence_after: float
    final_text_like: bool


@dataclass
class HeuristicSignals:
    text_like_ratio: float
    has_table_markers: bool
    has_legal_structure: bool


class LegalErrorRecoverySystem:
    """Heuristic error recovery system for legal documents (stub).

    This implements detection of common failure modes and simulated recovery
    strategies that improve a confidence score and text-likeness flag.
    """

    def analyze_failure_causes(self, data: bytes) -> FailureAnalysis:
        text = self._safe_decode(data)
        signals = self._signals(text)
        causes: List[str] = []
        # Heuristic on original bytes: high control-byte ratio indicates scan/binary
        control_bytes = sum(1 for b in data if b < 32 and b not in (9, 10, 13))
        control_ratio = control_bytes / max(1, len(data))
        if signals.text_like_ratio < 0.1 or control_ratio > 0.1:
            causes.append("poor_scan_quality")
        if signals.has_table_markers:
            causes.append("complex_table_structure")
        if not signals.has_legal_structure:
            causes.append("legal_formatting_issues")
        if "corrupted" in text.lower():
            causes.append("corrupted_pdf_structure")
        if not causes:
            causes.append("unknown")
        return FailureAnalysis(failure_causes=causes)

    def recover(self, data: bytes, *, base_confidence: float = 0.6) -> RecoveryReport:
        analysis = self.analyze_failure_causes(data)
        applied: List[RecoveryStepResult] = []
        confidence = base_confidence
        text_like = self._signals(self._safe_decode(data)).text_like_ratio >= 0.2

        for cause in analysis.failure_causes:
            if cause == "poor_scan_quality":
                res = self._apply_enhanced_ocr_preprocessing(data)
                applied.append(
                    RecoveryStepResult(
                        step="enhanced_ocr", applied=True, detail=res
                    )
                )
                confidence = max(confidence, 0.8)
                text_like = True
            elif cause == "complex_table_structure":
                res = self._use_specialized_table_extraction(data)
                applied.append(
                    RecoveryStepResult(
                        step="table_extraction", applied=True, detail=res
                    )
                )
                confidence = max(confidence, 0.78)
            elif cause == "legal_formatting_issues":
                res = self._apply_legal_document_templates(data)
                applied.append(
                    RecoveryStepResult(
                        step="legal_templates", applied=True, detail=res
                    )
                )
                confidence = max(confidence, 0.75)
            elif cause == "corrupted_pdf_structure":
                res = self._attempt_pdf_repair_and_reprocess(data)
                applied.append(
                    RecoveryStepResult(step="pdf_repair", applied=True, detail=res)
                )
                confidence = max(confidence, 0.7)
            else:
                applied.append(
                    RecoveryStepResult(
                        step="noop", applied=False, detail="no-op for unknown"
                    )
                )

        recovered = confidence >= 0.75 and text_like
        requires_manual = not recovered
        return RecoveryReport(
            recovered=recovered,
            requires_manual=requires_manual,
            applied_strategies=applied,
            confidence_before=base_confidence,
            confidence_after=confidence,
            final_text_like=text_like,
        )

    # --- Strategy implementations (stubs) ---

    def _apply_enhanced_ocr_preprocessing(self, data: bytes) -> str:
        return "deskew+contrast+denoise+premium_ocr"

    def _use_specialized_table_extraction(self, data: bytes) -> str:
        return "table_detector+cell_ocr"

    def _apply_legal_document_templates(self, data: bytes) -> str:
        return "legal_heading_normalizer+numbering_hints"

    def _attempt_pdf_repair_and_reprocess(self, data: bytes) -> str:
        return "qpdf_repair+re-extract"

    # --- Heuristics ---

    def _safe_decode(self, data: bytes) -> str:
        try:
            return data.decode("utf-8", errors="ignore")
        except Exception:
            return ""

    def _signals(self, text: str) -> HeuristicSignals:
        # Approximate text-like ratio: letters and spaces vs total
        if not text:
            return HeuristicSignals(0.0, False, False)
        letters = len(re.findall(r"[A-Za-z0-9\s]", text))
        ratio = letters / max(1, len(text))
        has_table = ("|" in text and "---" in text) or "+-" in text
        has_legal = bool(
            re.search(r"\b(Section|Article|Part)\b\s*\d+", text, re.IGNORECASE)
        )
        return HeuristicSignals(ratio, has_table, has_legal)
