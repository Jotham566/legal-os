from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from legal_os.db import Base
from legal_os.services.json_storage import RawJsonStorageService
from legal_os.services.consistency import ConsistencyChecker
from legal_os.storage import LocalStorage, artifact_key


def setup_db(tmp_path):
    engine = create_engine(f"sqlite+pysqlite:///{tmp_path}/test.db", future=True)
    Base.metadata.create_all(bind=engine)
    return engine


def test_check_and_reconcile_missing_xml(tmp_path):
    # Prepare DB with JSON only
    engine = setup_db(tmp_path)
    with Session(engine, future=True) as db:
        # Store JSON record
        svc = RawJsonStorageService(db)
        with db.begin():
            svc.store(
                document_id="d1",
                version_id="v1",
                raw_json_content={"content": [{"id": "sec1", "text": "Hello"}]},
                overall_confidence=0.9,
                provenance={"title": "Test", "jurisdiction": "ke"},
            )
        # Use LocalStorage for artifact simulation
        uploads = tmp_path / "uploads"
        uploads.mkdir()

        # Service-level check (inconsistent: JSON present, XML missing)
        checker = ConsistencyChecker(db, storage=LocalStorage(str(uploads)))
        report = checker.check(document_id="d1", version_id="v1")
        assert report.has_json is True
        assert report.has_xml is False
        assert report.consistent is False

        # Reconcile creates missing XML
        report2 = checker.reconcile(document_id="d1", version_id="v1")
        assert report2.has_xml is True
        # Ensure file present
        key = artifact_key("d1", "v1", "akn.xml")
        assert (uploads / key).exists()
