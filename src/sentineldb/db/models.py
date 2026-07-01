"""SQLAlchemy ORM models for SentinelDB's own persistence layer.

Schema uses standard PostgreSQL types only (no vendor extensions)
so it deploys to Supabase without modification.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import TIMESTAMP, Boolean, Float, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func

from sentineldb.db.session import tenant_context


def get_current_tenant_id() -> uuid.UUID:
    """Helper to fetch the current tenant ID for defaults."""
    tid = tenant_context.get()
    if tid is None:
        raise ValueError("Cannot persist model without an active tenant context")
    return tid


class Base(DeclarativeBase):
    pass


class TenantMixin:
    """Mixin to automatically enforce multi-tenancy columns."""

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
        default=get_current_tenant_id,
    )


class TenantORM(Base):
    __tablename__ = "tenants"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    billing_status: Mapped[str] = mapped_column(String(64), nullable=False, default="active")
    stripe_customer_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    plan_tier: Mapped[str] = mapped_column(String(64), nullable=False, default="free")
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )


class IncidentORM(TenantMixin, Base):
    __tablename__ = "incidents"

    incident_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    instance_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    alert_type: Mapped[str] = mapped_column(String(64), nullable=False)
    severity: Mapped[str] = mapped_column(String(16), nullable=False)
    metric_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    threshold_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    triggered_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="queued")
    raw_payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )


class IncidentReportORM(TenantMixin, Base):
    __tablename__ = "incident_reports"

    report_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    incident_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    rca_strength: Mapped[str] = mapped_column(String(16), nullable=False)
    root_cause_summary: Mapped[str] = mapped_column(Text, nullable=False)
    why_most_likely: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    evidence: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    runbook_reference: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    safe_next_actions: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    requires_approval: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    missing_evidence: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    llm_used: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    generated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )


class ThresholdConfigORM(TenantMixin, Base):
    __tablename__ = "threshold_configs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    instance_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    metric_name: Mapped[str] = mapped_column(String(128), nullable=False)
    warning_threshold: Mapped[float] = mapped_column(Float, nullable=False)
    critical_threshold: Mapped[float] = mapped_column(Float, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
