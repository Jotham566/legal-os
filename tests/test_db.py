from __future__ import annotations

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from legal_os.db import Base
from legal_os.models import Document, DocumentVersion


def test_create_tables_and_insert_select(tmp_path):
    # Use a temporary SQLite file DB for isolation
    db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite+pysqlite:///{db_path}", future=True)

    # Create tables
    Base.metadata.create_all(bind=engine)

    # Insert a document and a version
    with Session(engine, future=True) as session:
        doc = Document(title="Test Doc")
        session.add(doc)
        session.flush()  # get doc.id

        v1 = DocumentVersion(document_id=doc.id, version_number=1, content={"hello": "world"})
        session.add(v1)
        session.commit()

    # Query back
    with Session(engine, future=True) as session:
        docs = session.scalars(select(Document)).all()
        assert len(docs) == 1
        assert docs[0].title == "Test Doc"

        versions = session.scalars(select(DocumentVersion)).all()
        assert len(versions) == 1
        assert versions[0].version_number == 1
        assert versions[0].content["hello"] == "world"
