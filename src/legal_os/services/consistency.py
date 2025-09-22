from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from sqlalchemy.orm import Session

from ..models import RawJsonStorage
from ..storage import Storage, artifact_key, get_storage


@dataclass
class ConsistencyReport:
    document_id: str
    version_id: str
    has_json: bool
    has_xml: bool
    json_checksum: Optional[str]
    xml_present: bool
    consistent: bool


@dataclass
class ConsistencyChecker:
    db: Session
    storage: Optional[Storage] = None

    def __post_init__(self) -> None:
        if self.storage is None:
            self.storage = get_storage()

    def check(self, *, document_id: str, version_id: str) -> ConsistencyReport:
        rec: Optional[RawJsonStorage] = (
            self.db.query(RawJsonStorage)
            .filter(
                RawJsonStorage.document_id == document_id,
                RawJsonStorage.version_id == version_id,
            )
            .first()
        )
        has_json = rec is not None
        json_checksum = rec.content_checksum if rec else None
        xml_key = artifact_key(document_id, version_id, "akn.xml")
        xml_present = self.storage.exists(xml_key)  # type: ignore[union-attr]
        # If both present, define consistent as presence match
        # (deep checksum comparison could be added)
        consistent = (has_json and xml_present) or (not has_json and not xml_present)
        return ConsistencyReport(
            document_id=document_id,
            version_id=version_id,
            has_json=has_json,
            has_xml=xml_present,
            json_checksum=json_checksum,
            xml_present=xml_present,
            consistent=consistent,
        )

    def reconcile(self, *, document_id: str, version_id: str) -> ConsistencyReport:
        """Naive reconciliation: if JSON exists and XML missing, re-generate and store XML.
        If XML exists but JSON missing, do nothing (manual intervention).
        """
        report = self.check(document_id=document_id, version_id=version_id)
        if report.has_json and not report.has_xml:
            # regenerate XML artifact
            rec = (
                self.db.query(RawJsonStorage)
                .filter(
                    RawJsonStorage.document_id == document_id,
                    RawJsonStorage.version_id == version_id,
                )
                .first()
            )
            if rec is not None:
                from .akn import transform_to_akn, validate_akn_xml

                payload = {
                    "metadata": rec.provenance,
                    "content": rec.raw_json_content.get("content", []),
                }
                xml_bytes = transform_to_akn(payload)
                validate_akn_xml(xml_bytes)
                key = artifact_key(document_id, version_id, "akn.xml")
                import io

                buf = io.BytesIO(xml_bytes)
                self.storage.put_object(key, buf, len(xml_bytes))  # type: ignore[union-attr]
        # return updated report
        return self.check(document_id=document_id, version_id=version_id)
