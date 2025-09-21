from __future__ import annotations

import re
from typing import List, Tuple

from pydantic import BaseModel, Field


class GroundednessChecks(BaseModel):
    exact_text_match: float = Field(ge=0.0, le=1.0)
    contextual_accuracy: float = Field(ge=0.0, le=1.0)
    numbers_precision: float = Field(ge=0.0, le=1.0)
    dates_precision: float = Field(ge=0.0, le=1.0)
    cross_reference_integrity: float = Field(ge=0.0, le=1.0)


class GroundednessReport(BaseModel):
    checks: GroundednessChecks
    overall: float = Field(ge=0.0, le=1.0)
    requires_re_extraction: bool
    failed_checks: List[str] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)


def _normalize(s: str) -> str:
    s = s.lower().strip()
    # Collapse whitespace
    s = re.sub(r"\s+", " ", s)
    return s


def _find_best_alignment(extracted: str, source: str) -> Tuple[int | None, float]:
    """Return (start_index, match_ratio) best alignment of extracted in source.

    match_ratio is fraction of matching characters at the best start.
    """
    if not extracted:
        return None, 0.0
    if extracted in source:
        return source.index(extracted), 1.0
    # Brute-force best char match ratio over possible windows
    best_ratio = 0.0
    best_idx: int | None = None
    n = len(extracted)
    for i in range(0, max(0, len(source) - n + 1)):
        window = source[i : i + n]
        matches = sum(1 for a, b in zip(extracted, window) if a == b)
        ratio = matches / n
        if ratio > best_ratio:
            best_ratio = ratio
            best_idx = i
            if ratio == 1.0:
                break
    return best_idx, best_ratio


def _numbers(tokens: str) -> List[str]:
    return re.findall(r"\b\d+(?:[.,]\d+)?%?\b", tokens)


def _dates(tokens: str) -> List[str]:
    months = (
        "january|february|march|april|may|june|july|august|september|october|november|december"
    )
    pat = rf"\b\d{{1,2}}\s+(?:{months})\s+\d{{4}}\b"
    return re.findall(pat, tokens, flags=re.IGNORECASE)


def _cross_refs(tokens: str) -> List[str]:
    return re.findall(
        r"\b(section|sec\.|part|schedule)\s+[A-Za-z0-9]+\b",
        tokens,
        flags=re.IGNORECASE,
    )


def _boundary_ok_left(ctx: str) -> bool:
    if ctx == "":
        return True
    ch = ctx[-1]
    return bool(re.match(r"[a-z0-9\)\]\.,;:\s]", ch))


def _boundary_ok_right(ctx: str) -> bool:
    if ctx == "":
        return True
    ch = ctx[0]
    return bool(re.match(r"[a-z0-9\(\[\.,;:\s]", ch))


class GroundednessValidator:
    """Enhanced groundedness verification (spec 1.4.1)."""

    def verify(self, extracted_text: str, source_text: str) -> GroundednessReport:
        notes: List[str] = []
        ex_norm = _normalize(extracted_text)
        src_norm = _normalize(source_text)
        if not ex_norm:
            checks = GroundednessChecks(
                exact_text_match=0.0,
                contextual_accuracy=0.0,
                numbers_precision=0.0,
                dates_precision=0.0,
                cross_reference_integrity=0.0,
            )
            return GroundednessReport(
                checks=checks,
                overall=0.0,
                requires_re_extraction=True,
                failed_checks=[
                    "exact_text_match",
                    "contextual_accuracy",
                    "numbers_precision",
                    "dates_precision",
                    "cross_reference_integrity",
                ],
                notes=notes,
            )

        idx, exact_ratio = _find_best_alignment(ex_norm, src_norm)

        # Contextual accuracy: check neighbors around match window if located
        ctx_score = 0.0
        if idx is not None:
            n = len(ex_norm)
            left_ctx = src_norm[max(0, idx - 10) : idx]
            right_ctx = src_norm[idx + n : idx + n + 10]
            # Accept alnum OR whitespace/punctuation boundaries as OK
            left_ok = _boundary_ok_left(left_ctx)
            right_ok = _boundary_ok_right(right_ctx)
            ctx_score = 1.0 if (left_ok and right_ok) else 0.9
        else:
            # No clear alignment found; degrade
            ctx_score = max(0.0, min(1.0, exact_ratio * 0.8))

        # Numbers and dates precision: fraction of extracted tokens present in source
        ex_nums = _numbers(ex_norm)
        ex_dates = _dates(ex_norm)
        ex_refs = _cross_refs(ex_norm)
        num_score = 1.0
        if ex_nums:
            matched = sum(1 for n in ex_nums if n in src_norm)
            num_score = matched / len(ex_nums)
        date_score = 1.0
        if ex_dates:
            matched = sum(1 for d in ex_dates if d.lower() in src_norm)
            date_score = matched / len(ex_dates)
        ref_score = 1.0
        if ex_refs:
            matched = sum(1 for r in ex_refs if r.lower() in src_norm)
            ref_score = matched / len(ex_refs)

        checks = GroundednessChecks(
            exact_text_match=max(0.0, min(1.0, exact_ratio)),
            contextual_accuracy=max(0.0, min(1.0, ctx_score)),
            numbers_precision=max(0.0, min(1.0, num_score)),
            dates_precision=max(0.0, min(1.0, date_score)),
            cross_reference_integrity=max(0.0, min(1.0, ref_score)),
        )

        overall = (
            checks.exact_text_match
            + checks.contextual_accuracy
            + checks.numbers_precision
            + checks.dates_precision
            + checks.cross_reference_integrity
        ) / 5.0

        failed: List[str] = []
        if checks.exact_text_match < 0.995:
            failed.append("exact_text_match")
        if checks.contextual_accuracy < 0.95:
            failed.append("contextual_accuracy")
        if checks.numbers_precision < 1.0:
            failed.append("numbers_precision")
        if checks.dates_precision < 1.0:
            failed.append("dates_precision")
        if checks.cross_reference_integrity < 1.0:
            failed.append("cross_reference_integrity")

        requires_re = overall < 0.99

        return GroundednessReport(
            checks=checks,
            overall=max(0.0, min(1.0, overall)),
            requires_re_extraction=requires_re,
            failed_checks=failed,
            notes=notes,
        )
