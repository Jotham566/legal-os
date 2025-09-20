from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from legal_os.db import Base
from legal_os.audit import log_event, verify_chain


def test_audit_chain_and_tamper_detection(tmp_path):
    engine = create_engine(f"sqlite+pysqlite:///{tmp_path/'a.db'}", future=True)
    Base.metadata.create_all(bind=engine)

    with Session(engine, future=True) as session:
        # Add two events
        log_event(session, actor="u1", action="create", entity_type="doc", entity_id="1")
        e2 = log_event(
            session,
            actor="u1",
            action="update",
            entity_type="doc",
            entity_id="1",
            meta={"x": 1},
        )
        session.commit()

        # Verify chain OK
        v = verify_chain(session)
        assert v.ok

        # Tamper with second event (reassign dict to ensure change tracking)
        e2.meta = {"x": 999}
        session.commit()

        v2 = verify_chain(session)
        assert not v2.ok
        assert v2.invalid_index == 1
