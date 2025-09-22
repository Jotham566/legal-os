"""
Add audit_events, processing_sessions, and raw_json_storage tables

Revision ID: c8a4e0c2c9f1
Revises: 96739250c4ed
Create Date: 2025-09-22
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "c8a4e0c2c9f1"
down_revision = "96739250c4ed"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # audit_events
    op.create_table(
        "audit_events",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("actor", sa.String(length=256), nullable=False),
        sa.Column("action", sa.String(length=256), nullable=False),
        sa.Column("entity_type", sa.String(length=128), nullable=False),
        sa.Column("entity_id", sa.String(length=64), nullable=False),
        sa.Column("meta", sa.JSON(), nullable=False),
        sa.Column("prev_hash", sa.String(length=64), nullable=True),
        sa.Column("hash", sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_audit_events_hash"), "audit_events", ["hash"], unique=False
    )

    # processing_sessions
    op.create_table(
        "processing_sessions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("progress", sa.Integer(), nullable=False),
        sa.Column("eta_seconds", sa.Integer(), nullable=True),
        sa.Column("checkpoints", sa.JSON(), nullable=False),
        sa.Column("last_error", sa.String(length=1024), nullable=True),
        sa.Column("source_key", sa.String(length=512), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # raw_json_storage
    op.create_table(
        "raw_json_storage",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("document_id", sa.String(length=255), nullable=False),
        sa.Column("version_id", sa.String(length=255), nullable=False),
        sa.Column("raw_json_content", sa.JSON(), nullable=False),
        sa.Column("raw_json_size_kb", sa.Integer(), nullable=False),
        sa.Column("overall_confidence", sa.Float(), nullable=False),
        sa.Column("processing_logs", sa.JSON(), nullable=False),
        sa.Column("provenance", sa.JSON(), nullable=False),
        sa.Column("content_checksum", sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "document_id", "version_id", name="uq_raw_json_doc_ver"
        ),
    )
    op.create_index(
        op.f("ix_raw_json_storage_document_id"),
        "raw_json_storage",
        ["document_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_raw_json_storage_version_id"),
        "raw_json_storage",
        ["version_id"],
        unique=False,
    )
    op.create_index(
        "ix_raw_json_confidence",
        "raw_json_storage",
        ["overall_confidence"],
        unique=False,
    )
    op.create_index(
        "ix_raw_json_created_at",
        "raw_json_storage",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    # raw_json_storage
    op.drop_index("ix_raw_json_created_at", table_name="raw_json_storage")
    op.drop_index("ix_raw_json_confidence", table_name="raw_json_storage")
    op.drop_index(op.f("ix_raw_json_storage_version_id"), table_name="raw_json_storage")
    op.drop_index(op.f("ix_raw_json_storage_document_id"), table_name="raw_json_storage")
    op.drop_table("raw_json_storage")

    # processing_sessions
    op.drop_table("processing_sessions")

    # audit_events
    op.drop_index(op.f("ix_audit_events_hash"), table_name="audit_events")
    op.drop_table("audit_events")
