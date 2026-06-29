"""Tests for core Pydantic models and enums."""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from sentineldb.core.enums import AlertType, EvidenceStatus, IncidentStatus, RCAStrength, Severity
from sentineldb.core.models import (
    AlertPayload,
    CandidateCause,
    EvidenceBundle,
    EvidenceItem,
    IncidentReport,
    RunbookMatch,
    SafeAction,
)


# ---------------------------------------------------------------------------
# AlertPayload
# ---------------------------------------------------------------------------


def test_alert_payload_valid_roundtrip() -> None:
    payload = AlertPayload(
        instance_id="db-demo-01",
        alert_type=AlertType.cpu_high,
        severity=Severity.P1,
        metric_value=91.3,
        threshold_value=80.0,
    )
    data = payload.model_dump()
    restored = AlertPayload(**data)
    assert restored.instance_id == "db-demo-01"
    assert restored.alert_type == AlertType.cpu_high


def test_alert_payload_missing_instance_id_raises() -> None:
    with pytest.raises(ValidationError):
        AlertPayload(alert_type=AlertType.cpu_high, severity=Severity.P1)  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# EvidenceItem
# ---------------------------------------------------------------------------


def test_evidence_item_unavailable_value_none_valid() -> None:
    item = EvidenceItem(
        source="pg_stat_activity",
        label="active_connections",
        value=None,
        status=EvidenceStatus.UNAVAILABLE,
        display_text="active_connections: UNAVAILABLE",
    )
    assert item.status == EvidenceStatus.UNAVAILABLE
    assert item.value is None


def test_evidence_item_ok_value_none_raises() -> None:
    with pytest.raises(ValidationError):
        EvidenceItem(
            source="pg_stat_activity",
            label="active_connections",
            value=None,
            status=EvidenceStatus.OK,
            display_text="active_connections: None",
        )


def test_evidence_item_has_id() -> None:
    item = EvidenceItem(
        source="pg",
        label="conn",
        value=42.0,
        status=EvidenceStatus.OK,
        display_text="conn: 42",
    )
    assert item.id
    assert len(item.id) == 36  # UUID4 string


# ---------------------------------------------------------------------------
# EvidenceBundle
# ---------------------------------------------------------------------------


def test_evidence_bundle_all_unavailable() -> None:
    items = [
        EvidenceItem(
            source="pg", label=f"m{i}", value=None,
            status=EvidenceStatus.UNAVAILABLE, display_text=f"m{i}: UNAVAILABLE"
        )
        for i in range(3)
    ]
    bundle = EvidenceBundle(instance_id="db-01", items=items)
    assert bundle.all_unavailable is True


def test_evidence_bundle_not_all_unavailable_when_mixed() -> None:
    items = [
        EvidenceItem(source="pg", label="a", value=1.0, status=EvidenceStatus.OK, display_text="a: 1"),
        EvidenceItem(source="pg", label="b", value=None, status=EvidenceStatus.UNAVAILABLE, display_text="b: UNAVAILABLE"),
    ]
    bundle = EvidenceBundle(instance_id="db-01", items=items)
    assert bundle.all_unavailable is False


def test_evidence_bundle_get() -> None:
    item = EvidenceItem(source="pg", label="active_connections", value=42.0, status=EvidenceStatus.OK, display_text="42")
    bundle = EvidenceBundle(instance_id="db-01", items=[item])
    assert bundle.get("active_connections") is item
    assert bundle.get("nonexistent") is None


# ---------------------------------------------------------------------------
# CandidateCause
# ---------------------------------------------------------------------------


def test_candidate_cause_empty_why_raises() -> None:
    with pytest.raises(ValidationError):
        CandidateCause(
            cause_type="connection_saturation",
            rca_strength=RCAStrength.High,
            why_most_likely=[],  # must be non-empty
        )


def test_candidate_cause_valid() -> None:
    cause = CandidateCause(
        cause_type="connection_saturation",
        rca_strength=RCAStrength.High,
        why_most_likely=["Active connections at 85% of max_connections"],
    )
    assert cause.rca_strength == RCAStrength.High


# ---------------------------------------------------------------------------
# IncidentReport
# ---------------------------------------------------------------------------


def test_incident_report_json_serializable() -> None:
    item = EvidenceItem(
        source="pg", label="active_connections", value=423.0,
        status=EvidenceStatus.OK, display_text="423 active connections"
    )
    report = IncidentReport(
        incident_id="inc-001",
        rca_strength=RCAStrength.High,
        root_cause_summary="Connection pool is saturated.",
        why_most_likely=["423 of 500 connections active"],
        evidence=[item],
    )
    json_str = report.model_dump_json()
    assert "Connection pool" in json_str
    assert "active_connections" in json_str


def test_incident_report_llm_used_defaults_false() -> None:
    report = IncidentReport(
        incident_id="inc-002",
        rca_strength=RCAStrength.Low,
        root_cause_summary="Unknown cause.",
        why_most_likely=["Insufficient evidence"],
        evidence=[],
    )
    assert report.llm_used is False


def test_incident_report_datetime_no_precision_loss() -> None:
    ts = datetime(2026, 6, 27, 12, 0, 0, 123456, tzinfo=timezone.utc)
    item = EvidenceItem(
        source="pg", label="x", value=1.0,
        status=EvidenceStatus.OK, display_text="x: 1",
        timestamp=ts,
    )
    data = item.model_dump()
    assert data["timestamp"].microsecond == 123456
