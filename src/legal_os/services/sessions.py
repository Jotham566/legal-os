from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from ..models import ProcessingSession


def UTC() -> datetime:
    return datetime.now(timezone.utc)


class SessionService:
    def __init__(self, db: Session):
        self.db = db

    def create(self, source_key: Optional[str] = None) -> ProcessingSession:
        ps = ProcessingSession(
            status="running",
            progress=0,
            eta_seconds=None,
            checkpoints={},
            last_error=None,
            source_key=source_key,
        )
        self.db.add(ps)
        self.db.flush()
        return ps

    def get(self, session_id: str) -> Optional[ProcessingSession]:
        return self.db.get(ProcessingSession, session_id)

    def update(
        self,
        session_id: str,
        *,
        status: Optional[str] = None,
        progress: Optional[int] = None,
        eta_seconds: Optional[int] = None,
        checkpoint: Optional[dict] = None,
        error: Optional[str] = None,
    ) -> Optional[ProcessingSession]:
        ps = self.get(session_id)
        if not ps:
            return None
        if status is not None:
            ps.status = status
        if progress is not None:
            ps.progress = max(0, min(100, progress))
        if eta_seconds is not None:
            ps.eta_seconds = max(0, eta_seconds)
        if checkpoint is not None:
            # merge by key
            ps.checkpoints.update(checkpoint)
        if error is not None:
            ps.last_error = error
            ps.status = ps.status if ps.status != "completed" else "completed"
        ps.updated_at = UTC()
        self.db.add(ps)
        self.db.flush()
        return ps

    def complete(self, session_id: str) -> Optional[ProcessingSession]:
        return self.update(session_id, status="completed", progress=100, eta_seconds=0)

    def fail(self, session_id: str, error: str) -> Optional[ProcessingSession]:
        return self.update(session_id, status="failed", error=error)
