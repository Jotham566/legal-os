from __future__ import annotations

import re
from typing import List

from pydantic import BaseModel, Field


class ComplianceChecks(BaseModel):
    citation_accuracy: float = Field(ge=0.0, le=1.0)
    cross_reference_integrity: float = Field(ge=0.0, le=1.0)
    legal_numbering_compliance: float = Field(ge=0.0, le=1.0)
    amendment_tracking: float = Field(ge=0.0, le=1.0)
    definition_consistency: float = Field(ge=0.0, le=1.0)
    hierarchical_structure: float = Field(ge=0.0, le=1.0)
    mandatory_sections: float = Field(ge=0.0, le=1.0)


class ComplianceReport(BaseModel):
    checks: ComplianceChecks
    overall_compliance: float = Field(ge=0.0, le=1.0)
    requires_review: bool
    issues: List[str] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)


class LegalComplianceValidator:
    """Heuristic validator for legal compliance (spec 1.3.2).

    This is a baseline heuristic implementation for dev/testing. It analyzes raw text
    for common legal structural cues and assigns confidences per check. In production,
    this should operate on structured extraction results with precise validations.
    """

    def validate_legal_structure(
        self, content: bytes, content_type: str | None
    ) -> ComplianceReport:
        try:
            text = content.decode("utf-8", errors="ignore")
        except Exception:  # pragma: no cover
            text = ""

        issues: List[str] = []
        notes: List[str] = []

        if content_type:
            notes.append(content_type)

        if not text.strip():
            checks = ComplianceChecks(
                citation_accuracy=0.0,
                cross_reference_integrity=0.0,
                legal_numbering_compliance=0.0,
                amendment_tracking=0.0,
                definition_consistency=0.0,
                hierarchical_structure=0.0,
                mandatory_sections=0.0,
            )
            return ComplianceReport(
                checks=checks,
                overall_compliance=0.0,
                requires_review=True,
                issues=["empty_or_non_text_content"],
                notes=notes,
            )

        # Heuristic signals
        ratio = min(
            1.0,
            max(0.0, sum(1 for ch in text if ch.isprintable()) / max(1, len(text))),
        )
        has_section_headings = bool(
            re.search(r"(?m)^\d{1,3}\.[ \t]+.+$", text)
        )
        has_part_headings = bool(re.search(r"(?i)\bpart\s+[ivx]+\b", text))
        has_cross_refs = bool(
            re.search(r"(?i)\b(section|part|schedule)\s+[A-Za-z0-9]+\b", text)
        )
        has_definitions = bool(
            re.search(r"(?i)['\"][^'\"]{3,64}['\"][ ]+means", text)
        )
        has_amendments = bool(re.search(r"(?i)amend|repeal|substitute", text))
        has_numbering = has_section_headings or has_part_headings
        has_mandatory = bool(
            re.search(r"(?i)short title|commencement|definitions", text)
        )

        # Assign confidences
        citation_accuracy = 0.6 * ratio + (0.2 if has_cross_refs else 0.0)
        cross_reference_integrity = 0.5 * ratio + (
            0.25 if has_cross_refs and has_numbering else 0.0
        )
        legal_numbering_compliance = 0.5 * ratio + (0.3 if has_numbering else 0.0)
        amendment_tracking = 0.4 * ratio + (0.3 if has_amendments else 0.0)
        definition_consistency = 0.4 * ratio + (0.3 if has_definitions else 0.0)
        hierarchical_structure = 0.5 * ratio + (
            0.3 if has_part_headings and has_section_headings else 0.0
        )
        mandatory_sections = 0.5 * ratio + (0.3 if has_mandatory else 0.0)

        # Clamp to [0,1]
        def clamp(x: float) -> float:
            return max(0.0, min(1.0, x))

        checks = ComplianceChecks(
            citation_accuracy=clamp(citation_accuracy),
            cross_reference_integrity=clamp(cross_reference_integrity),
            legal_numbering_compliance=clamp(legal_numbering_compliance),
            amendment_tracking=clamp(amendment_tracking),
            definition_consistency=clamp(definition_consistency),
            hierarchical_structure=clamp(hierarchical_structure),
            mandatory_sections=clamp(mandatory_sections),
        )

        # Overall score = average
        total = (
            checks.citation_accuracy
            + checks.cross_reference_integrity
            + checks.legal_numbering_compliance
            + checks.amendment_tracking
            + checks.definition_consistency
            + checks.hierarchical_structure
            + checks.mandatory_sections
        )
        overall = total / 7.0

        # Issues list
        if not has_numbering:
            issues.append("numbering_scheme_weak")
        if not has_cross_refs:
            issues.append("cross_references_missing")
        if not has_definitions:
            issues.append("definitions_missing")
        if not has_mandatory:
            issues.append("mandatory_sections_missing")

        requires_review = overall < 0.98

        return ComplianceReport(
            checks=checks,
            overall_compliance=clamp(overall),
            requires_review=requires_review,
            issues=issues,
            notes=notes,
        )
