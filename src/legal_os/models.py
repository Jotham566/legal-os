from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional
from uuid import uuid4

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    title: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    versions: Mapped[List["DocumentVersion"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="DocumentVersion.version_number",
    )


class DocumentVersion(Base):
    __tablename__ = "document_versions"
    __table_args__ = (
        UniqueConstraint("document_id", "version_number", name="uq_document_version"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    document_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("documents.id"), nullable=False, index=True
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )

    document: Mapped[Document] = relationship(back_populates="versions")


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    actor: Mapped[str] = mapped_column(String(256), nullable=False)
    action: Mapped[str] = mapped_column(String(256), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(128), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(64), nullable=False)
    meta: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    # Tamper-evident chaining: hash of previous event + current payload
    prev_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)


class ProcessingSession(Base):
    __tablename__ = "processing_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    status: Mapped[str] = mapped_column(String(32), default="running", nullable=False)
    progress: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    eta_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    checkpoints: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    last_error: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    source_key: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)


class RawJsonStorage(Base):
    __tablename__ = "raw_json_storage"
    __table_args__ = (
        UniqueConstraint("document_id", "version_id", name="uq_raw_json_doc_ver"),
        Index("ix_raw_json_confidence", "overall_confidence"),
        Index("ix_raw_json_created_at", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    document_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    version_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    raw_json_content: Mapped[dict] = mapped_column(JSON, nullable=False)
    raw_json_size_kb: Mapped[int] = mapped_column(Integer, nullable=False)
    overall_confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    processing_logs: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    provenance: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    content_checksum: Mapped[str] = mapped_column(String(64), nullable=False, default="")
