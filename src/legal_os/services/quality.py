from __future__ import annotations

from typing import Tuple


def simple_text_ratio(data: bytes) -> float:
    if not data:
        return 0.0
    # Heuristic: consider ascii printable bytes as text-like
    text_like = sum(1 for b in data if 9 <= b <= 13 or 32 <= b <= 126)
    ratio = text_like / max(1, len(data))
    # Clamp
    return max(0.0, min(1.0, float(ratio)))


essential_types = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.oasis.opendocument.text",
}


def assess_quality(
    content: bytes,
    *,
    content_type: str | None,
    size: int,
) -> Tuple[float, list[str], bool, float, int | None]:
    issues: list[str] = []
    # Size checks (very small or very large)
    if size <= 0:
        issues.append("Empty file")
    if size > 500 * 1024 * 1024:
        issues.append("File too large")

    # Content type checks
    if content_type and content_type not in essential_types:
        issues.append("Unsupported content type")

    # Text extractability heuristic
    ratio = simple_text_ratio(content)
    needs_ocr = ratio < 0.05 and (content_type == "application/pdf")

    # Page count heuristic (very rough): assume one page per 2^16 bytes for PDFs
    page_count = None
    if content_type == "application/pdf" and size > 0:
        page_count = max(1, size // 65536)

    # Base score from ratio and penalties
    score = 0.6 * ratio + 0.4
    # Penalize issues
    if issues:
        score -= 0.1 * len(issues)
    # Clamp to [0,1]
    score = max(0.0, min(1.0, score))

    return (
        score,
        issues,
        needs_ocr,
        ratio,
        page_count,
    )
