from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from typing import Iterable

from ..settings import Settings


@dataclass
class Metadata:
    filename: str
    content_type: str
    size: int
    sha256: str
    extension: str
    title_guess: str | None
    label: str
    confidence: float


ALLOWED_TYPES = {
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "application/vnd.oasis.opendocument.text": ".odt",
}


def _classify(content_type: str) -> tuple[str, float]:
    # Simple rule-based classifier tied to MIME
    if content_type == "application/pdf":
        return ("pdf", 0.99)
    if content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return ("docx", 0.98)
    if content_type == "application/vnd.oasis.opendocument.text":
        return ("odt", 0.97)
    return ("unknown", 0.5)


def extract_metadata(filename: str, content_type: str, data: bytes) -> Metadata:
    sha = hashlib.sha256(data).hexdigest()
    size = len(data)
    ext = ALLOWED_TYPES.get(content_type) or (os.path.splitext(filename)[1] or "")
    # Basic title guess: filename without extension
    title = os.path.splitext(os.path.basename(filename))[0] if filename else None
    label, conf = _classify(content_type)
    return Metadata(
        filename=filename,
        content_type=content_type,
        size=size,
        sha256=sha,
        extension=ext,
        title_guess=title,
        label=label,
        confidence=conf,
    )


def validate_metadata(meta: Metadata, settings: Settings) -> list[str]:
    issues: list[str] = []
    max_bytes = settings.max_upload_mb * 1024 * 1024
    if meta.size <= 0:
        issues.append("empty_file")
    if meta.size > max_bytes:
        issues.append("too_large")
    if meta.content_type not in ALLOWED_TYPES:
        issues.append("unsupported_type")
    return issues


def is_duplicate(sha256: str, known_hashes: Iterable[str] | None = None) -> bool:
    if known_hashes is None:
        return False
    return sha256 in set(known_hashes)
