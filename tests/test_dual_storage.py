from __future__ import annotations

from io import BytesIO

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from legal_os.db import Base
from legal_os.services.dual_storage import DualStorageCoordinator
from legal_os.services.json_storage import RawJsonStorageService


class FakeStorage:
    def __init__(self):
        self.objects: dict[str, bytes] = {}

    def put_object(self, key: str, stream, length: int) -> None:
        self.objects[key] = stream.read(length)

    def url_for(self, key: str):
        return None

    def delete_object(self, key: str) -> None:
        self.objects.pop(key, None)

    def exists(self, key: str) -> bool:
        return key in self.objects


def setup_db(tmp_path):
    engine = create_engine(f"sqlite+pysqlite:///{tmp_path}/test.db", future=True)
    Base.metadata.create_all(bind=engine)
    return engine


def test_dual_storage_success(tmp_path):
    engine = setup_db(tmp_path)
    with Session(engine, future=True) as db:
        storage = FakeStorage()
        coord = DualStorageCoordinator(db=db, storage=storage)
        # Begin transaction explicitly to ensure rollback would be possible
        with db.begin():
            coord.store_json_and_xml(
                document_id="d1",
                version_id="v1",
                raw_json_content={"content": [{"id": "sec1", "text": "Hello"}]},
                overall_confidence=0.9,
                provenance={"title": "Test", "jurisdiction": "ke"},
            )
        # Verify DB record staged
        svc = RawJsonStorageService(db)
        rec = svc.get(document_id="d1", version_id="v1")
        assert rec is not None
        # Verify XML stored
        from legal_os.storage import artifact_key

        key = artifact_key("d1", "v1", "akn.xml")
        assert storage.exists(key)
        assert storage.objects[key].startswith(b"<?xml")


def test_dual_storage_xml_failure_rolls_back(tmp_path, monkeypatch):
    engine = setup_db(tmp_path)
    with Session(engine, future=True) as db:
        storage = FakeStorage()
        coord = DualStorageCoordinator(db=db, storage=storage)

        class BrokenStorage(FakeStorage):
            def put_object(self, key, stream, length):
                raise RuntimeError("boom")

        broken = BrokenStorage()
        try:
            with db.begin():
                coord.storage = broken
                coord.store_json_and_xml(
                    document_id="d2",
                    version_id="v1",
                    raw_json_content={"content": [{"id": "sec1", "text": "Hello"}]},
                    overall_confidence=0.9,
                    provenance={"title": "Test", "jurisdiction": "ke"},
                )
        except RuntimeError:
            pass
        # After failure, ensure no DB record (transaction should be rolled back by context manager)
        svc = RawJsonStorageService(db)
        rec = svc.get(document_id="d2", version_id="v1")
        assert rec is None
