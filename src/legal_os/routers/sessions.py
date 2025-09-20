from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from typing import AsyncIterator
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from ..db import session_scope
from ..models import ProcessingSession
from ..schemas import (
    ProcessingSessionCreate,
    ProcessingSessionOut,
    ProcessingSessionUpdate,
)
from ..services.sessions import SessionService

router = APIRouter(prefix="/sessions", tags=["sessions"])


def _to_out(ps: ProcessingSession) -> ProcessingSessionOut:
    return ProcessingSessionOut(
        id=ps.id,
        created_at=ps.created_at,
        updated_at=ps.updated_at,
        status=ps.status,
        progress=ps.progress,
        eta_seconds=ps.eta_seconds,
        checkpoints=ps.checkpoints,
        last_error=ps.last_error,
        source_key=ps.source_key,
    )


@router.post("/", response_model=ProcessingSessionOut)
def create_session(payload: ProcessingSessionCreate) -> ProcessingSessionOut:
    with session_scope() as db:
        svc = SessionService(db)
        ps = svc.create(source_key=payload.source_key)
        return _to_out(ps)


@router.get("/{session_id}", response_model=ProcessingSessionOut)
def get_session(session_id: str) -> ProcessingSessionOut:
    with session_scope() as db:
        svc = SessionService(db)
        ps = svc.get(session_id)
        if not ps:
            raise HTTPException(status_code=404, detail="Session not found")
        return _to_out(ps)


@router.patch("/{session_id}", response_model=ProcessingSessionOut)
def update_session(session_id: str, payload: ProcessingSessionUpdate) -> ProcessingSessionOut:
    with session_scope() as db:
        svc = SessionService(db)
        ps = svc.update(
            session_id,
            status=payload.status,
            progress=payload.progress,
            eta_seconds=payload.eta_seconds,
            checkpoint=payload.checkpoint,
            error=payload.error,
        )
        if not ps:
            raise HTTPException(status_code=404, detail="Session not found")
        return _to_out(ps)


@router.get("/{session_id}/events")
async def stream_session_events(session_id: str) -> StreamingResponse:
    # Simple polling loop to simulate server-sent events (SSE) via text/event-stream
    async def event_generator() -> AsyncIterator[str]:
        last_snapshot = None
        while True:
            with session_scope() as db:
                svc = SessionService(db)
                ps = svc.get(session_id)
                if not ps:
                    yield "event: error\n" "data: {\"detail\": \"not found\"}\n\n"
                    break
                snap = {
                    "id": ps.id,
                    "ts": datetime.now(timezone.utc).isoformat(),
                    "status": ps.status,
                    "progress": ps.progress,
                    "eta_seconds": ps.eta_seconds,
                    "checkpoints": ps.checkpoints,
                    "last_error": ps.last_error,
                }
                data = json.dumps(snap)
                if data != last_snapshot:
                    yield f"data: {data}\n\n"
                    last_snapshot = data
                if ps.status in ("completed", "failed"):
                    break
            await asyncio.sleep(1)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
