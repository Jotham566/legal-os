from __future__ import annotations

from datetime import timedelta
import time

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from legal_os.db import Base
from legal_os.models import Base as _Base  # noqa: F401  # keep import path sanity for tools
from legal_os.services.documents import add_version, create_document, get_version_as_of


def test_version_increment_and_temporal_query(tmp_path):
    engine = create_engine(f"sqlite+pysqlite:///{tmp_path/'v.db'}", future=True)
    Base.metadata.create_all(bind=engine)

    with Session(engine, future=True) as session:
        doc = create_document(session, title="T")
        v1 = add_version(session, doc.id, {"n": 1})
        # ensure a measurable time delta between versions
        time.sleep(0.01)
        v2 = add_version(session, doc.id, {"n": 2})
        session.commit()

        assert v1.version_number == 1
        assert v2.version_number == 2

        # Temporal query
        at_time = v2.created_at - timedelta(milliseconds=1)
        got = get_version_as_of(session, doc.id, at_time)
        assert got is not None
        assert got.version_number == 1


def test_immutability_violation_raises(tmp_path):
    engine = create_engine(f"sqlite+pysqlite:///{tmp_path/'v.db'}", future=True)
    Base.metadata.create_all(bind=engine)

    with Session(engine, future=True) as session:
        doc = create_document(session, title="T")
        v1 = add_version(session, doc.id, {"n": 1})
        session.commit()

        v1.content = {"n": 111}
        session.add(v1)
        raised = False
        try:
            session.commit()
        except ValueError as e:  # from immutability hook
            raised = True
            assert "immutable" in str(e)
        finally:
            session.rollback()
        assert raised
