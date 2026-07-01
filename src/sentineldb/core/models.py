"""Core Pydantic v2 domain models for SentinelDB."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from sentineldb.core.enums import (
    AlertType,
    EvidenceStatus,
    RCAStrength,
    Severity,
)


class AlertPayload(BaseModel):
    """Inbound alert describing a DB incident trigger."""

    model_config = ConfigDict(frozen=True)

    tenant_id: uuid.UUID | None = None
    instance_id: str
    alert_type: AlertType
    severity: Severity
    metric_value: float | None = None
    threshold_value: float | None = None
    triggered_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    raw_payload: dict[str, Any] = Field(default_factory=dict)


class EvidenceItem(BaseModel):
    """A single piece of collected diagnostic evidence."""

    model_config = ConfigDict(frozen=True)

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source: str
    label: str
    value: float | str | None
    unit: str | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    status: EvidenceStatus
    raw_reference: str | None = None
    display_text: str

    @classmethod
    def unavailable(cls, source: str, label: str) -> EvidenceItem:
        return cls(
            source=source,
            label=label,
            value=None,
            status=EvidenceStatus.UNAVAILABLE,
            display_text=f"{label}: UNAVAILABLE",
        )

    @model_validator(mode="after")
    def value_required_when_ok(self) -> EvidenceItem:
        if self.status != EvidenceStatus.UNAVAILABLE and self.value is None:
            raise ValueError(f"EvidenceItem.value must be set when status={self.status.value}")
        return self


class EvidenceBundle(BaseModel):
    """Collected evidence from all sources for one incident."""

    model_config = ConfigDict(frozen=True)

    instance_id: str
    collected_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    items: list[EvidenceItem] = Field(default_factory=list)

    def get(self, label: str) -> EvidenceItem | None:
        for item in self.items:
            if item.label == label:
                return item
        return None

    @property
    def all_unavailable(self) -> bool:
        return bool(self.items) and all(i.status == EvidenceStatus.UNAVAILABLE for i in self.items)


class CandidateCause(BaseModel):
    """A ranked root-cause hypothesis produced by the deterministic analyzer."""

    model_config = ConfigDict(frozen=True)

    cause_type: str
    rca_strength: RCAStrength
    why_most_likely: list[str] = Field(min_length=1)
    supporting_evidence_ids: list[str] = Field(default_factory=list)
    excluded_causes: list[str] = Field(default_factory=list)
    missing_evidence: list[str] = Field(default_factory=list)


class RunbookMatch(BaseModel):
    """A runbook matched to the current incident."""

    model_config = ConfigDict(frozen=True)

    path: str
    title: str
    relevant_snippet: str
    score: float


class SafeAction(BaseModel):
    """An approved read-only diagnostic action."""

    model_config = ConfigDict(frozen=True)

    label: str
    description: str
    catalog_key: str  # key in DIAGNOSTIC_CATALOG


class IncidentReport(BaseModel):
    """The final structured RCA report for an incident."""

    model_config = ConfigDict(frozen=True)

    report_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    incident_id: str
    rca_strength: RCAStrength
    root_cause_summary: str
    why_most_likely: list[str]
    evidence: list[EvidenceItem]
    runbook_reference: RunbookMatch | None = None
    safe_next_actions: list[SafeAction] = Field(default_factory=list)
    requires_approval: list[str] = Field(default_factory=list)
    missing_evidence: list[str] = Field(default_factory=list)
    llm_used: bool = False
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
