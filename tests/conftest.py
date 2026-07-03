"""Shared test fixtures for SentinelDB test suite."""

from __future__ import annotations

import pytest

from sentineldb.core.enums import (
    AlertType,
    EvidenceStatus,
    RCAStrength,
    Severity,
)
from sentineldb.core.models import (
    AlertPayload,
    CandidateCause,
    EvidenceBundle,
    EvidenceItem,
    IncidentReport,
    SafeAction,
)


@pytest.fixture
def sample_alert_payload() -> AlertPayload:
    """A realistic AlertPayload for CPU high on the demo instance."""
    return AlertPayload(
        instance_id="db-demo-01",
        alert_type=AlertType.cpu_high,
        severity=Severity.P1,
        metric_value=95.0,
        threshold_value=80.0,
    )


@pytest.fixture
def sample_evidence_items() -> list[EvidenceItem]:
    """A realistic set of evidence items from a PostgreSQL collector."""
    return [
        EvidenceItem(
            source="pg_stat_activity",
            label="active_connections",
            value=423.0,
            status=EvidenceStatus.OK,
            display_text="active_connections: 423.0",
        ),
        EvidenceItem(
            source="pg",
            label="max_connections",
            value=500.0,
            status=EvidenceStatus.OK,
            display_text="max_connections: 500.0",
        ),
        EvidenceItem(
            source="pg_stat_activity",
            label="waiting_connections",
            value=38.0,
            status=EvidenceStatus.OK,
            display_text="waiting_connections: 38.0",
        ),
        EvidenceItem(
            source="pg",
            label="replication_lag",
            value=0.5,
            status=EvidenceStatus.OK,
            display_text="replication_lag: 0.5",
        ),
    ]


@pytest.fixture
def sample_evidence_bundle(sample_evidence_items: list[EvidenceItem]) -> EvidenceBundle:
    """An EvidenceBundle with realistic connection saturation data."""
    return EvidenceBundle(
        instance_id="db-demo-01",
        items=sample_evidence_items,
    )


@pytest.fixture
def sample_candidate_cause() -> CandidateCause:
    """A high-confidence connection saturation cause."""
    return CandidateCause(
        cause_type="connection_saturation",
        rca_strength=RCAStrength.High,
        why_most_likely=["Active connections (423) are at 84.6% of max_connections (500)."],
    )


@pytest.fixture
def sample_incident_report(sample_evidence_items: list[EvidenceItem]) -> IncidentReport:
    """A complete IncidentReport for notification/rendering tests."""
    return IncidentReport(
        incident_id="test-incident-001",
        rca_strength=RCAStrength.High,
        root_cause_summary="Database connection pool saturation: 423 active connections.",
        why_most_likely=["Active connections (423) are at 84.6% of max_connections (500)."],
        evidence=sample_evidence_items,
        safe_next_actions=[
            SafeAction(
                label="Check active connections",
                description="View currently executing queries.",
                catalog_key="active_connections",
            ),
        ],
        requires_approval=["Killing sessions (pg_terminate_backend)"],
        missing_evidence=[],
        llm_used=False,
    )
