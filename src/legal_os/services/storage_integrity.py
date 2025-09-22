from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Dict, Tuple, cast

from jsonschema import Draft202012Validator, ValidationError


# Minimal baseline schema for our raw JSON payloads
RAW_JSON_SCHEMA: Dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "properties": {
        "content": {"type": ["object", "array", "string", "number", "boolean", "null"]},
        "metadata": {"type": "object"},
        "overall_confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
    },
    "required": ["content"],
    "additionalProperties": True,
}

_validator = Draft202012Validator(RAW_JSON_SCHEMA)


def validate_payload(payload: Dict[str, Any]) -> Tuple[bool, str | None]:
    try:
        _validator.validate(payload)
        return True, None
    except ValidationError as e:  # pragma: no cover - exercised in tests
        return False, e.message


def compute_checksum(data: Dict[str, Any]) -> str:
    # Deterministic checksum: canonical JSON
    blob = json.dumps(data, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def verify_checksum(data: Dict[str, Any], checksum: str) -> bool:
    return compute_checksum(data) == checksum


@dataclass
class VersionRef:
    document_id: str
    version_id: str


def verify_keys_match_version(
    doc_id: str, ver_id: str, stored_doc_id: str, stored_ver_id: str
) -> bool:
    return doc_id == stored_doc_id and ver_id == stored_ver_id


# Simple local backup/restore helpers for JSON content

def backup_to_file(path: str, data: Dict[str, Any]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))


def restore_from_file(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return cast(Dict[str, Any], json.load(f))
