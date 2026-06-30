"""Initial schema — incidents and incident_reports tables."""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "incidents",
        sa.Column("incident_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("instance_id", sa.String(255), nullable=False),
        sa.Column("alert_type", sa.String(64), nullable=False),
        sa.Column("severity", sa.String(16), nullable=False),
        sa.Column("metric_value", sa.Float, nullable=True),
        sa.Column("threshold_value", sa.Float, nullable=True),
        sa.Column("triggered_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="queued"),
        sa.Column("raw_payload", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_incidents_instance_id", "incidents", ["instance_id"])

    op.create_table(
        "incident_reports",
        sa.Column("report_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("incident_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("rca_strength", sa.String(16), nullable=False),
        sa.Column("root_cause_summary", sa.Text, nullable=False),
        sa.Column("why_most_likely", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("evidence", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("runbook_reference", postgresql.JSONB, nullable=True),
        sa.Column("safe_next_actions", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("requires_approval", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("missing_evidence", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("llm_used", sa.Boolean, nullable=False, server_default="false"),
        sa.Column(
            "generated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["incident_id"], ["incidents.incident_id"]),
    )
    op.create_index("ix_incident_reports_incident_id", "incident_reports", ["incident_id"])


def downgrade() -> None:
    op.drop_table("incident_reports")
    op.drop_table("incidents")
