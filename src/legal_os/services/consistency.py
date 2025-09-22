from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, cast
import hashlib

from sqlalchemy.orm import Session

from ..models import RawJsonStorage
from ..storage import Storage, artifact_key, get_storage
from .akn import validate_akn_xml


@dataclass
class ConsistencyReport:
    document_id: str
    version_id: str
    has_json: bool
    has_xml: bool
    json_checksum: Optional[str]
    xml_present: bool
    consistent: bool
    xml_checksum_matches: Optional[bool] = None
    xml_well_formed: Optional[bool] = None


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
        sidecar_key = artifact_key(document_id, version_id, "akn.xml.sha256")
        xml_present = self.storage.exists(xml_key)  # type: ignore[union-attr]
        xml_checksum_matches: Optional[bool] = None
        xml_well_formed: Optional[bool] = None
        if xml_present:
            try:
                data = self.storage.get_object(xml_key)  # type: ignore[union-attr]
                # validate XML well-formedness
                try:
                    validate_akn_xml(data)
                    xml_well_formed = True
                except Exception:
                    xml_well_formed = False
                # compare checksum if sidecar exists
                if self.storage.exists(sidecar_key):  # type: ignore[union-attr]
                    side = self.storage.get_object(sidecar_key)  # type: ignore[union-attr]
                    stored = side.decode("utf-8").strip()
                    actual = hashlib.sha256(data).hexdigest()
                    xml_checksum_matches = stored == actual
            except Exception:
                # unable to fetch xml; treat as missing
                xml_present = False
        # Define consistent: json and xml both present and xml_well_formed and checksum matches
        # (if available)
        consistent = False
        if has_json and xml_present:
            checks = [
                xml_well_formed is True,
            ]
            if xml_checksum_matches is not None:
                checks.append(xml_checksum_matches)
            consistent = all(checks)
        elif not has_json and not xml_present:
            consistent = True
        return ConsistencyReport(
            document_id=document_id,
            version_id=version_id,
            has_json=has_json,
            has_xml=xml_present,
            json_checksum=json_checksum,
            xml_present=xml_present,
            consistent=consistent,
            xml_checksum_matches=xml_checksum_matches,
            xml_well_formed=xml_well_formed,
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
                import io
                import hashlib as _hashlib

                payload = {
                    "metadata": rec.provenance,
                    "content": rec.raw_json_content.get("content", []),
                }
                xml_bytes = transform_to_akn(payload)
                validate_akn_xml(xml_bytes)
                key = artifact_key(document_id, version_id, "akn.xml")
                sidecar_key = artifact_key(document_id, version_id, "akn.xml.sha256")

                storage: Storage = cast(Storage, self.storage)
                buf = io.BytesIO(xml_bytes)
                storage.put_object(key, buf, len(xml_bytes))
                sha256 = _hashlib.sha256(xml_bytes).hexdigest()
                side_buf = io.BytesIO(sha256.encode("utf-8"))
                storage.put_object(sidecar_key, side_buf, len(sha256))
        # return updated report
        return self.check(document_id=document_id, version_id=version_id)
