"""Add tenant_id multi-tenancy

Revision ID: d1b7b3cd934c
Revises: 0001
Create Date: 2026-07-01 05:12:03.061301

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'd1b7b3cd934c'
down_revision: str | None = '0001'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create tenants table
    op.create_table(
        "tenants",
        sa.Column("tenant_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("billing_status", sa.String(length=64), nullable=False),
        sa.Column("stripe_customer_id", sa.String(length=255), nullable=True),
        sa.Column("plan_tier", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("tenant_id"),
    )

    # Add tenant_id to incidents
    op.add_column("incidents", sa.Column("tenant_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index("ix_incidents_tenant_id", "incidents", ["tenant_id"])

    # Add tenant_id to incident_reports
    op.add_column("incident_reports", sa.Column("tenant_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index("ix_incident_reports_tenant_id", "incident_reports", ["tenant_id"])

    # Add tenant_id to threshold_configs
    op.add_column("threshold_configs", sa.Column("tenant_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index("ix_threshold_configs_tenant_id", "threshold_configs", ["tenant_id"])


def downgrade() -> None:
    op.drop_index("ix_threshold_configs_tenant_id", table_name="threshold_configs")
    op.drop_column("threshold_configs", "tenant_id")

    op.drop_index("ix_incident_reports_tenant_id", table_name="incident_reports")
    op.drop_column("incident_reports", "tenant_id")

    op.drop_index("ix_incidents_tenant_id", table_name="incidents")
    op.drop_column("incidents", "tenant_id")

    op.drop_table("tenants")
