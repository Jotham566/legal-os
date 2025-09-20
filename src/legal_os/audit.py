from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import AuditEvent


def _hash_event(
    prev_hash: Optional[str],
    actor: str,
    action: str,
    entity_type: str,
    entity_id: str,
    meta: dict,
) -> str:
    payload = {
        "prev": prev_hash or "",
        "actor": actor,
        "action": action,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "meta": meta,
    }
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def log_event(
    session: Session,
    *,
    actor: str,
    action: str,
    entity_type: str,
    entity_id: str,
    meta: Optional[dict] = None,
) -> AuditEvent:
    meta = meta or {}
    prev: Optional[str] = session.scalar(
        select(AuditEvent.hash).order_by(
            AuditEvent.created_at.desc(), AuditEvent.id.desc()
        )
    )
    h = _hash_event(prev, actor, action, entity_type, entity_id, meta)
    ev = AuditEvent(
        actor=actor,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        meta=meta,
        prev_hash=prev,
        hash=h,
    )
    session.add(ev)
    return ev


@dataclass
class ChainVerification:
    ok: bool
    invalid_index: Optional[int] = None


def verify_chain(session: Session) -> ChainVerification:
    events = list(
        session.scalars(
            select(AuditEvent).order_by(
                AuditEvent.created_at.asc(), AuditEvent.id.asc()
            )
        )
    )
    prev: Optional[str] = None
    for idx, ev in enumerate(events):
        expected = _hash_event(
            prev, ev.actor, ev.action, ev.entity_type, ev.entity_id, ev.meta
        )
        if ev.hash != expected or ev.prev_hash != (prev or None):
            return ChainVerification(ok=False, invalid_index=idx)
        prev = ev.hash
    return ChainVerification(ok=True)
