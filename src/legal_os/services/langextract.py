from __future__ import annotations

import re
from typing import List, Tuple

from pydantic import BaseModel

from ..schemas import (
    CharSpan,
    CrossReference,
    LangExtractResult,
    LegalClassification,
    LegalTerm,
)


class LangExtractClient(BaseModel):
    """Heuristic stub for LangExtract legal enhancement.

    In production, this would call a Gemini-powered service to detect legal terms,
    cross-references, and classifications with high accuracy and detailed grounding.
    Here, we use simple regex-based heuristics to simulate behavior for tests.
    """

    def analyze(self, content: bytes, content_type: str | None) -> LangExtractResult:
        text: str
        try:
            text = content.decode("utf-8", errors="ignore")
        except Exception:  # pragma: no cover - defensive
            text = ""

        if not text.strip():
            return LangExtractResult(
                overall_confidence=0.0,
                notes=["empty_or_non_text_content"],
            )

        terms: List[LegalTerm] = []
        cross_refs: List[CrossReference] = []
        classes: List[LegalClassification] = []
        notes: List[str] = []

        # Definitions: patterns like "In this Act, 'term' means ..." or "\"term\" means"
        for m in re.finditer(
            r"(?i)(?:in this act[, ]+)?['\"]([^'\"]{3,64})['\"][ ]+means",
            text,
        ):
            term = m.group(1)
            span = CharSpan(start=m.start(1), end=m.end(1))
            terms.append(
                LegalTerm(text=term, kind="definition", span=span, confidence=0.85)
            )

        # Entities: capitalized multi-word sequences possibly representing legal entities
        for m in re.finditer(
            r"\b([A-Z][a-z]+(?: [A-Z][a-z]+){1,3})\b",
            text,
        ):
            candidate = m.group(1)
            # Heuristic filter for common words
            if candidate.lower() in {"in this", "short title"}:
                continue
            terms.append(
                LegalTerm(
                    text=candidate,
                    kind="entity",
                    span=CharSpan(start=m.start(1), end=m.end(1)),
                    confidence=0.6,
                )
            )

        # Amounts and rates
        for m in re.finditer(
            r"\b(\d{1,3}(?:,\d{3})*(?:\.\d+)?)[ ]*(?:ugx|shs|usd|%)\b",
            text,
            re.IGNORECASE,
        ):
            token = m.group(0)
            terms.append(
                LegalTerm(
                    text=token,
                    kind="amount" if not token.endswith("%") else "rate",
                    span=CharSpan(start=m.start(0), end=m.end(0)),
                    confidence=0.8,
                )
            )

        # Dates
        months = (
            "January|February|March|April|May|June|July|August|September|October|November|December"
        )
        date_pattern = rf"\b(\d{{1,2}}\s+({months})\s+\d{{4}})\b"
        for m in re.finditer(date_pattern, text):
            terms.append(
                LegalTerm(
                    text=m.group(1),
                    kind="date",
                    span=CharSpan(start=m.start(1), end=m.end(1)),
                    confidence=0.8,
                )
            )

        # Section headings: lines starting with number + dot + title
        for m in re.finditer(
            r"(?m)^(\d{1,3})\.[ ]+(.+)$",
            text,
        ):
            heading = m.group(2).strip()
            if heading:
                terms.append(
                    LegalTerm(
                        text=heading,
                        kind="section_heading",
                        span=CharSpan(start=m.start(2), end=m.end(2)),
                        confidence=0.75,
                    )
                )

        # Cross-references: "Section X", "Part Y", "Schedule Z"
        for m in re.finditer(
            r"(?i)\b(section|part|schedule)\s+([A-Za-z0-9]+)\b",
            text,
        ):
            ref_text = m.group(0)
            cross_refs.append(
                CrossReference(
                    text=ref_text,
                    source_span=CharSpan(start=m.start(0), end=m.end(0)),
                    target_hint=f"{m.group(1).lower()}_{m.group(2)}",
                    confidence=0.7,
                )
            )

        # Classifications based on keywords
        keywords: List[Tuple[str, str]] = [
            ("penalty", "penalty"),
            ("commence", "commencement"),
            ("amend", "amendment"),
            ("rate", "tax_rate"),
            ("uganda|kenya|tanzania|rwanda|burundi", "jurisdiction"),
        ]
        for pattern, category in keywords:
            for m in re.finditer(pattern, text, re.IGNORECASE):
                classes.append(
                    LegalClassification(
                        category=category,  # type: ignore[arg-type]
                        span=CharSpan(start=m.start(0), end=m.end(0)),
                        confidence=0.65,
                    )
                )

        # Overall confidence heuristic: proportion of text-like content
        text_chars = sum(1 for ch in text if ch.isprintable())
        ratio = min(1.0, max(0.0, text_chars / max(1, len(text))))
        overall = min(1.0, 0.5 + 0.5 * ratio)

        if content_type and "pdf" in content_type.lower():
            notes.append("pdf_input")
        return LangExtractResult(
            terms=terms,
            cross_references=cross_refs,
            classifications=classes,
            overall_confidence=overall,
            notes=notes,
        )
