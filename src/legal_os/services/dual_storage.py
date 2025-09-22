from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from typing import Optional, cast

from sqlalchemy.orm import Session

from ..models import ProcessingSession, RawJsonStorage
from ..storage import Storage, artifact_key, get_storage
from .akn import transform_to_akn, validate_akn_xml, AKNError
from .json_storage import RawJsonStorageService


@dataclass
class DualStorageCoordinator:
    """Coordinates atomic-like write of JSON and AKN XML artifacts.

    JSON is persisted in DB via RawJsonStorageService; XML is persisted to object storage
    under an artifact key. If XML write fails, the JSON insert is rolled back. If JSON
    insert fails, no XML is written. This approximates atomicity across stores.
    """

    db: Session
    storage: Optional[Storage] = None

    def __post_init__(self) -> None:
        if self.storage is None:
            self.storage = get_storage()

    def _require_storage(self) -> Storage:
        assert self.storage is not None, "storage not initialized"
        return cast(Storage, self.storage)

    def _get_or_create_session(
        self, key: str, document_id: str, version_id: str
    ) -> ProcessingSession:
        sess = (
            self.db.query(ProcessingSession)
            .filter(ProcessingSession.source_key == key)
            .first()
        )
        if sess is None:
            sess = ProcessingSession(
                status="running",
                progress=0,
                checkpoints={
                    "document_id": document_id,
                    "version_id": version_id,
                },
                source_key=key,
            )
            self.db.add(sess)
        return sess

    def store_json_and_xml(
        self,
        *,
        document_id: str,
        version_id: str,
        raw_json_content: dict,
        overall_confidence: float = 0.0,
        processing_logs: Optional[dict] = None,
        provenance: Optional[dict] = None,
        validate_schema: bool = True,
    ) -> None:
        json_service = RawJsonStorageService(self.db)

        # Stage 1: transform JSON -> AKN XML (bytes) and validate
        try:
            xml_bytes = transform_to_akn(
                {
                    "metadata": provenance or {},
                    "content": raw_json_content.get("content", []),
                }
            )
            validate_akn_xml(xml_bytes)
        except AKNError as e:
            raise ValueError(f"AKN transformation failed: {e}")

        # Stage 2: persist JSON (part of DB transaction), but skip if exists
        existing: Optional[RawJsonStorage] = json_service.get(
            document_id=document_id, version_id=version_id
        )
        if existing is None:
            rec = json_service.store(
                document_id=document_id,
                version_id=version_id,
                raw_json_content=raw_json_content,
                overall_confidence=overall_confidence,
                processing_logs=processing_logs,
                provenance=provenance,
                validate=validate_schema,
            )
        else:
            rec = existing

        # Stage 3: persist XML to object storage
        xml_key = artifact_key(document_id, version_id, "akn.xml")
        try:
            buf = BytesIO(xml_bytes)
            storage = self._require_storage()
            storage.put_object(xml_key, buf, len(xml_bytes))
        except Exception as e:
            # Attempt compensation: delete possibly written object
            try:
                storage = self._require_storage()
                storage.delete_object(xml_key)
            except Exception:
                pass
            # Roll back DB insert by expunging and raising, relying on caller
            # to rollback transaction
            if existing is None:
                self.db.expunge(rec)
            raise RuntimeError(f"Failed to store AKN XML artifact: {e}")

    def store_json_and_xml_idempotent(
        self,
        *,
        idempotency_key: str,
        document_id: str,
        version_id: str,
        raw_json_content: dict,
        overall_confidence: float = 0.0,
        processing_logs: Optional[dict] = None,
        provenance: Optional[dict] = None,
        validate_schema: bool = True,
    ) -> None:
        """Idempotent saga-like orchestration.

        Uses ProcessingSession.source_key to de-duplicate requests. If a session with
        the given idempotency_key exists and is completed, this becomes a no-op.
        """
        sess = self._get_or_create_session(idempotency_key, document_id, version_id)
        if sess.status == "completed":
            return
        sess.status = "running"
        sess.progress = 10
        self.db.flush()

        try:
            self.store_json_and_xml(
                document_id=document_id,
                version_id=version_id,
                raw_json_content=raw_json_content,
                overall_confidence=overall_confidence,
                processing_logs=processing_logs,
                provenance=provenance,
                validate_schema=validate_schema,
            )
            sess.progress = 100
            sess.status = "completed"
            self.db.flush()
        except Exception as e:
            sess.status = "failed"
            sess.last_error = str(e)
            self.db.flush()
            raise

    def delete_xml_artifact(self, *, document_id: str, version_id: str) -> None:
        xml_key = artifact_key(document_id, version_id, "akn.xml")
        try:
            storage = self._require_storage()
            storage.delete_object(xml_key)
        except Exception:
            # best effort
            pass
