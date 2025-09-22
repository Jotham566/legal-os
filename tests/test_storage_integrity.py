from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
import pytest

from legal_os.db import Base
from legal_os.services.json_storage import RawJsonStorageService
from legal_os.services.storage_integrity import (
    compute_checksum,
    verify_checksum,
    backup_to_file,
    restore_from_file,
    verify_keys_match_version,
)


@pytest.fixture
def db_session(tmp_path):
    engine = create_engine(f"sqlite+pysqlite:///{tmp_path/'test.db'}", future=True)
    Base.metadata.create_all(bind=engine)
    with Session(engine, future=True) as s:
        yield s


def test_schema_validation_failure(db_session):
    svc = RawJsonStorageService(db_session)
    with pytest.raises(ValueError):
        # overall_confidence invalid > 1.0 will raise
        svc.store(
            document_id="docX",
            version_id="v1",
            raw_json_content={"content": "nested wrong shape"},
            overall_confidence=1.2,
        )


def test_checksum_roundtrip_and_verify(db_session, tmp_path):
    svc = RawJsonStorageService(db_session)
    rec = svc.store(
        document_id="doc1",
        version_id="v1",
        raw_json_content={"a": 1, "b": [1, 2, 3]},
        overall_confidence=0.8,
    )
    db_session.commit()

    # Verify checksum matches stored payload
    assert verify_checksum(rec.raw_json_content, rec.content_checksum)

    # Backup and restore
    backup_path = tmp_path / "backup.json"
    backup_to_file(str(backup_path), rec.raw_json_content)
    restored = restore_from_file(str(backup_path))
    assert restored == rec.raw_json_content
    assert compute_checksum(restored) == rec.content_checksum


def test_keys_match_version():
    assert verify_keys_match_version("doc1", "v1", "doc1", "v1")
    assert not verify_keys_match_version("doc1", "v1", "doc1", "v2")
