"""
Tests for RCA renderer.
"""
from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest

from sentineldb.analysis.renderer import Renderer
from sentineldb.core.enums import AlertType, EvidenceStatus, RCAStrength, Severity
from sentineldb.core.models import (
    AlertPayload,
    CandidateCause,
    EvidenceBundle,
    EvidenceItem,
    RunbookMatch,
)


@pytest.fixture
def renderer() -> Renderer:
    return Renderer()


def _item(label: str, value: float | None = None, status: EvidenceStatus = EvidenceStatus.OK) -> EvidenceItem:
    return EvidenceItem(
        source="pg",
        label=label,
        value=value,
        status=status,
        display_text=f"{label}: {value if status == EvidenceStatus.OK else status.value}",
    )


def test_render_connection_saturation_report(renderer: Renderer) -> None:
    alert = AlertPayload(
        instance_id="db-1",
        alert_type=AlertType.cpu_high,
        severity=Severity.P1,
    )
    items = [
        _item("active_connections", 423.0),
        _item("waiting_connections", 38.0),
        _item("max_connections", 500.0),
    ]
    bundle = EvidenceBundle(instance_id="db-1", items=items)
    cause = CandidateCause(
        cause_type="connection_saturation",
        rca_strength=RCAStrength.High,
        why_most_likely=["Active connections near max"],
        supporting_evidence_ids=[i.id for i in items],
    )
    runbook = RunbookMatch(
        path="runbooks/high_cpu_connection_saturation.md",
        title="High CPU / Connection Saturation",
        relevant_snippet="## Symptoms...",
        score=0.8,
    )

    report = renderer.render(alert, cause, bundle, runbook)

    assert report.rca_strength == RCAStrength.High
    assert "saturation" in report.root_cause_summary.lower()
    assert len(report.evidence) == 3
    assert len(report.safe_next_actions) > 0
    assert any("Killing sessions" in r for r in report.requires_approval)
    assert report.runbook_reference is not None
    assert report.runbook_reference.path == "runbooks/high_cpu_connection_saturation.md"

    # Report serializable
    assert json.loads(report.model_dump_json())


def test_render_slow_query_scrubs_pii_from_summary(renderer: Renderer) -> None:
    alert = AlertPayload(
        instance_id="db-1",
        alert_type=AlertType.slow_query,
        severity=Severity.P2,
    )
    bundle = EvidenceBundle(instance_id="db-1", items=[_item("slow_query_count", 15000.0)])
    cause = CandidateCause(
        cause_type="slow_query_cpu_pressure",
        rca_strength=RCAStrength.Medium,
        why_most_likely=["Slow queries spiking"],
        supporting_evidence_ids=[],
    )

    report = renderer.render(alert, cause, bundle, None)

    # Values in summary should use display text, no explicit hostnames
    assert "db.internal" not in report.root_cause_summary
    assert "root_user" not in report.root_cause_summary


def test_render_partial_failure_missing_evidence(renderer: Renderer) -> None:
    alert = AlertPayload(
        instance_id="db-1",
        alert_type=AlertType.cpu_high,
        severity=Severity.P2,
    )
    bundle = EvidenceBundle(instance_id="db-1", items=[_item("cpu_utilization", 95.0)])
    cause = CandidateCause(
        cause_type="slow_query_cpu_pressure",
        rca_strength=RCAStrength.Medium,
        why_most_likely=["CPU is high"],
        missing_evidence=["slow_query_count"],
    )

    report = renderer.render(alert, cause, bundle, None)

    assert report.rca_strength == RCAStrength.Medium
    assert len(report.missing_evidence) == 1
    assert "slow_query_count" in report.missing_evidence[0]
    assert report.runbook_reference is None


def test_evidence_values_match_exactly(renderer: Renderer) -> None:
    alert = AlertPayload(instance_id="db-1", alert_type=AlertType.cpu_high, severity=Severity.P1)
    bundle = EvidenceBundle(
        instance_id="db-1",
        items=[_item("active_connections", 123.45)]
    )
    cause = CandidateCause(
        cause_type="unknown_cause",
        rca_strength=RCAStrength.Low,
        why_most_likely=["No rules fired"],
    )

    report = renderer.render(alert, cause, bundle, None)
    assert report.evidence[0].value == 123.45
