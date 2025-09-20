from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import event, select
from sqlalchemy.orm import Session, Mapper
from sqlalchemy.engine import Connection

from ..models import Document, DocumentVersion


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def create_document(session: Session, title: Optional[str] = None) -> Document:
    doc = Document(title=title)
    session.add(doc)
    session.flush()
    return doc


def add_version(session: Session, document_id: str, content: dict) -> DocumentVersion:
    # Determine next version number
    last_version = session.scalars(
        select(DocumentVersion)
        .where(DocumentVersion.document_id == document_id)
        .order_by(DocumentVersion.version_number.desc())
        .limit(1)
    ).first()
    next_num = 1 if last_version is None else last_version.version_number + 1
    ver = DocumentVersion(document_id=document_id, version_number=next_num, content=content)
    session.add(ver)
    session.flush()
    return ver


def get_version_as_of(
    session: Session, document_id: str, at: datetime
) -> Optional[DocumentVersion]:
    # Return the latest version created at or before timestamp
    return (
        session.scalars(
            select(DocumentVersion)
            .where(DocumentVersion.document_id == document_id)
            .where(DocumentVersion.created_at <= at)
            .order_by(DocumentVersion.created_at.desc())
            .limit(1)
        ).first()
    )


# Immutability enforcement: prevent updates to DocumentVersion rows after insert
@event.listens_for(DocumentVersion, "before_update", propagate=True)
def _deny_update(mapper: Mapper, connection: Connection, target: DocumentVersion) -> None:
    raise ValueError("DocumentVersion records are immutable and cannot be updated")
