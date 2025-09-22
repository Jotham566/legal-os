from __future__ import annotations

import math
from typing import Optional
from sqlalchemy.orm import Session

from ..models import RawJsonStorage
from .storage_integrity import compute_checksum, validate_payload


def _size_kb(payload: dict) -> int:
    # Rough size estimation using UTF-8 length of stringified JSON
    import json

    blob = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    return math.ceil(len(blob) / 1024)


class RawJsonStorageService:
    def __init__(self, db: Session):
        self.db = db

    def store(
        self,
        *,
        document_id: str,
        version_id: str,
        raw_json_content: dict,
        overall_confidence: float = 0.0,
        processing_logs: Optional[dict] = None,
        provenance: Optional[dict] = None,
        validate: bool = True,
    ) -> RawJsonStorage:
        if not (0.0 <= overall_confidence <= 1.0):
            raise ValueError("overall_confidence must be in [0,1]")
        if validate:
            ok, msg = validate_payload(
                {
                    "content": raw_json_content,
                    "metadata": provenance or {},
                    "overall_confidence": overall_confidence,
                }
            )
            if not ok:
                raise ValueError(f"raw_json_content failed schema validation: {msg}")
        sz_kb = _size_kb(raw_json_content)
        checksum = compute_checksum(raw_json_content)
        rec = RawJsonStorage(
            document_id=document_id,
            version_id=version_id,
            raw_json_content=raw_json_content,
            raw_json_size_kb=sz_kb,
            overall_confidence=overall_confidence,
            processing_logs=processing_logs or {},
            provenance=provenance or {},
            content_checksum=checksum,
        )
        self.db.add(rec)
        return rec

    def get(self, *, document_id: str, version_id: str) -> Optional[RawJsonStorage]:
        return (
            self.db.query(RawJsonStorage)
            .filter(
                RawJsonStorage.document_id == document_id,
                RawJsonStorage.version_id == version_id,
            )
            .first()
        )
