from __future__ import annotations

from typing import List, Literal

from pydantic import BaseModel

from ..schemas import QAValidationMetrics, QAValidationResult


class QAClient(BaseModel):
    """Heuristic stub for GPT QA validation layer.

    Simulates structure validation, reasoning verification, cross-reference validation,
    and compliance checks. Selects between 'gpt-5' and 'gpt-5-mini' heuristically.
    """

    def run_validate(self, content: bytes, content_type: str | None) -> QAValidationResult:
        try:
            text = content.decode("utf-8", errors="ignore")
        except Exception:  # pragma: no cover - defensive
            text = ""

        if not text.strip():
            # Return low-confidence empty analysis
            metrics = QAValidationMetrics(
                structure_valid=False,
                reasoning_ok=False,
                cross_references_ok=False,
                compliance_ok=False,
                structure_confidence=0.0,
                reasoning_confidence=0.0,
                cross_references_confidence=0.0,
                compliance_confidence=0.0,
            )
            return QAValidationResult(
                model_used="gpt-5-mini",
                corrections_applied=0,
                issues=["empty_or_non_text_content"],
                metrics=metrics,
                overall_confidence=0.0,
                notes=[],
            )

        # Text-likeness and simple structure heuristics
        printable = sum(1 for ch in text if ch.isprintable())
        ratio = min(1.0, max(0.0, printable / max(1, len(text))))

        has_sections = ("section" in text.lower()) or ("sec." in text.lower())
        has_refs = ("refer" in text.lower()) or ("see" in text.lower())
        has_legal_terms = any(t in text.lower() for t in ["amend", "penalty", "commence"])
        has_numbers = any(ch.isdigit() for ch in text)

        structure_valid = has_sections or has_numbers
        cross_ok = has_refs and has_sections
        reasoning_ok = has_legal_terms and structure_valid
        compliance_ok = structure_valid and ratio > 0.5

        # Confidence assignments
        structure_conf = 0.5 + 0.5 * ratio if structure_valid else 0.3 * ratio
        cross_conf = 0.5 * ratio + (0.2 if cross_ok else 0.0)
        reasoning_conf = 0.5 * ratio + (0.2 if reasoning_ok else 0.0)
        compliance_conf = 0.6 * ratio + (0.2 if compliance_ok else 0.0)

        # Model selection optimization: use mini for small/simple inputs
        selected_model: Literal["gpt-5", "gpt-5-mini"] = (
            "gpt-5-mini" if (len(text) < 5000 and ratio > 0.6) else "gpt-5"
        )

        issues: List[str] = []
        if not structure_valid:
            issues.append("structure_invalid")
        if not cross_ok:
            issues.append("cross_reference_weak")
        if not reasoning_ok:
            issues.append("reasoning_inconclusive")
        if not compliance_ok:
            issues.append("compliance_checks_failed")

        overall = min(
            1.0,
            max(0.0, (structure_conf + cross_conf + reasoning_conf + compliance_conf) / 4.0),
        )

        metrics = QAValidationMetrics(
            structure_valid=structure_valid,
            reasoning_ok=reasoning_ok,
            cross_references_ok=cross_ok,
            compliance_ok=compliance_ok,
            structure_confidence=structure_conf,
            reasoning_confidence=reasoning_conf,
            cross_references_confidence=cross_conf,
            compliance_confidence=compliance_conf,
        )

        notes: List[str] = []
        if content_type:
            notes.append(content_type)

        return QAValidationResult(
            model_used=selected_model,
            corrections_applied=0,
            issues=issues,
            metrics=metrics,
            overall_confidence=overall,
            notes=notes,
        )
