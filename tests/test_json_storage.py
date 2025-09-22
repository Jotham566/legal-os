from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
import pytest

from legal_os.db import Base
from legal_os.services.json_storage import RawJsonStorageService


@pytest.fixture
def db_session(tmp_path):
    engine = create_engine(f"sqlite+pysqlite:///{tmp_path/'test.db'}", future=True)
    Base.metadata.create_all(bind=engine)
    with Session(engine, future=True) as s:
        yield s


def test_store_and_get_json(db_session):
    svc = RawJsonStorageService(db_session)
    rec = svc.store(
        document_id="doc1",
        version_id="v1",
        raw_json_content={"a": 1, "b": "x"},
        overall_confidence=0.9,
        processing_logs={"steps": ["extract", "validate"]},
        provenance={"tools": ["docling", "langextract"]},
    )
    db_session.commit()

    assert rec.id is not None
    assert rec.raw_json_size_kb >= 1

    fetched = svc.get(document_id="doc1", version_id="v1")
    assert fetched is not None
    assert fetched.document_id == "doc1"
    assert fetched.version_id == "v1"
    assert fetched.overall_confidence == 0.9


def test_overall_confidence_bounds(db_session):
    svc = RawJsonStorageService(db_session)
    with pytest.raises(ValueError):
        svc.store(
            document_id="doc2",
            version_id="v1",
            raw_json_content={"ok": True},
            overall_confidence=1.5,
        )
