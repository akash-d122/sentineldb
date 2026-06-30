"""
Tests for RCA Analyzer rules.
Golden test scenarios matching the plan for V1A rules.
"""

from __future__ import annotations

import pytest

from sentineldb.analysis.rules import Analyzer
from sentineldb.core.enums import EvidenceStatus, RCAStrength
from sentineldb.core.models import EvidenceBundle, EvidenceItem


@pytest.fixture
def analyzer() -> Analyzer:
    return Analyzer()


def _item(
    label: str, value: float | None = None, status: EvidenceStatus = EvidenceStatus.OK
) -> EvidenceItem:
    return EvidenceItem(
        source="pg",
        label=label,
        value=value,
        status=status,
        display_text=f"{label}: {value if status == EvidenceStatus.OK else status.value}",
    )


def test_golden_db_unreachable_high(analyzer: Analyzer) -> None:
    bundle = EvidenceBundle(
        instance_id="db-1",
        items=[
            _item("active_connections", status=EvidenceStatus.UNAVAILABLE),
            _item("waiting_connections", status=EvidenceStatus.UNAVAILABLE),
            _item("replication_lag", status=EvidenceStatus.UNAVAILABLE),
        ],
    )
    causes = analyzer.rank_causes(bundle)
    assert len(causes) > 0
    top = causes[0]
    assert top.cause_type == "db_unreachable"
    assert top.rca_strength == RCAStrength.High


def test_golden_connection_saturation_high(analyzer: Analyzer) -> None:
    bundle = EvidenceBundle(
        instance_id="db-1",
        items=[
            _item("active_connections", 423.0),
            _item("max_connections", 500.0),
            _item("waiting_connections", 38.0),
        ],
    )
    causes = analyzer.rank_causes(bundle)
    assert len(causes) > 0
    top = causes[0]
    assert top.cause_type == "connection_saturation"
    assert top.rca_strength == RCAStrength.High
    assert "active connections" in " ".join(top.why_most_likely).lower()


def test_golden_connection_saturation_low(analyzer: Analyzer) -> None:
    bundle = EvidenceBundle(
        instance_id="db-1",
        items=[
            _item("active_connections", 300.0),  # 60% of 500
            _item("max_connections", 500.0),
            _item("waiting_connections", 0.0),
        ],
    )
    causes = analyzer.rank_causes(bundle)
    # The rule shouldn't rank it high; might not even return it if it's below 80%,
    # or return it as Low if we want to surface it. The plan says:
    # "connections 60% no waiting → connection_saturation Low or not primary"
    if not causes:
        # Not returned is fine
        pass
    else:
        assert (
            causes[0].cause_type != "connection_saturation"
            or causes[0].rca_strength == RCAStrength.Low
        )


def test_golden_slow_query_cpu_pressure_high(analyzer: Analyzer) -> None:
    bundle = EvidenceBundle(
        instance_id="db-1",
        items=[
            _item("slow_query_count", 12847.0),
            _item("cpu_utilization", 91.3),
        ],
    )
    causes = analyzer.rank_causes(bundle)
    assert len(causes) > 0
    top = causes[0]
    assert top.cause_type == "slow_query_cpu_pressure"
    assert top.rca_strength == RCAStrength.High


def test_golden_slow_query_cpu_pressure_medium(analyzer: Analyzer) -> None:
    bundle = EvidenceBundle(
        instance_id="db-1",
        items=[
            # Missing slow_query_count entirely
            _item("cpu_utilization", 91.3),
        ],
    )
    causes = analyzer.rank_causes(bundle)
    assert len(causes) > 0
    top = causes[0]
    assert top.cause_type == "slow_query_cpu_pressure"
    assert top.rca_strength == RCAStrength.Medium
    assert "slow_query_count" in " ".join(top.missing_evidence)


def test_golden_replication_lag_medium(analyzer: Analyzer) -> None:
    bundle = EvidenceBundle(
        instance_id="db-1",
        items=[
            _item("replication_lag", 120.0),
        ],
    )
    causes = analyzer.rank_causes(bundle)
    assert len(causes) > 0
    top = causes[0]
    assert top.cause_type == "replication_lag"
    assert top.rca_strength == RCAStrength.Medium
    assert "write_volume" in " ".join(top.missing_evidence)


def test_fallback_cause_when_no_rules_match(analyzer: Analyzer) -> None:
    """If no rules match, the analyzer must return an unknown_cause with Low strength."""
    bundle = EvidenceBundle(
        instance_id="db-1",
        items=[
            _item("active_connections", 10.0),
            _item("max_connections", 500.0),
            _item("waiting_connections", 0.0),
            _item("replication_lag", 0.0),
        ],
    )
    causes = analyzer.rank_causes(bundle)
    assert len(causes) > 0
    top = causes[0]
    assert top.cause_type == "unknown_cause"
    assert top.rca_strength == RCAStrength.Low
