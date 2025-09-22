from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from legal_os.db import Base
from legal_os.services.dual_storage import DualStorageCoordinator
from legal_os.storage import LocalStorage, artifact_key


class MemoryStorage(LocalStorage):
    # Reuse LocalStorage semantics with tmp base_dir created by tmp_path in test
    pass


def setup_db(tmp_path):
    engine = create_engine(f"sqlite+pysqlite:///{tmp_path}/test.db", future=True)
    Base.metadata.create_all(bind=engine)
    return engine


def test_idempotent_store(tmp_path):
    engine = setup_db(tmp_path)
    uploads = tmp_path / "uploads"
    uploads.mkdir()
    with Session(engine, future=True) as db:
        coord = DualStorageCoordinator(db=db, storage=MemoryStorage(str(uploads)))
        with db.begin():
            coord.store_json_and_xml_idempotent(
                idempotency_key="req-123",
                document_id="d1",
                version_id="v1",
                raw_json_content={"content": [{"id": "sec1", "text": "Hello"}]},
                overall_confidence=0.9,
                provenance={"title": "Test", "jurisdiction": "ke"},
            )
        # Second run should be no-op and not error
        with db.begin():
            coord.store_json_and_xml_idempotent(
                idempotency_key="req-123",
                document_id="d1",
                version_id="v1",
                raw_json_content={"content": [{"id": "sec1", "text": "Hello"}]},
                overall_confidence=0.9,
                provenance={"title": "Test", "jurisdiction": "ke"},
            )
        # Verify artifact exists
        key = artifact_key("d1", "v1", "akn.xml")
        assert (uploads / key).exists()
