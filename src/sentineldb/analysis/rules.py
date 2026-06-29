"""
Deterministic RCA rules engine.

Applies rules over an EvidenceBundle to rank CandidateCauses.
"""

from __future__ import annotations

from sentineldb.core.enums import RCAStrength
from sentineldb.core.models import CandidateCause, EvidenceBundle, EvidenceItem


class Analyzer:
    """Analyzes evidence bundles to determine candidate causes."""

    def rank_causes(self, bundle: EvidenceBundle) -> list[CandidateCause]:
        """Rank causes based on deterministic rules."""
        causes: list[CandidateCause] = []

        # 1. DB Unreachable
        if bundle.all_unavailable:
            causes.append(self._rule_db_unreachable(bundle))
            return causes  # Short-circuit if nothing is available

        # Apply standard rules
        if c := self._rule_connection_saturation(bundle):
            causes.append(c)

        if c := self._rule_slow_query_cpu_pressure(bundle):
            causes.append(c)

        if c := self._rule_replication_lag(bundle):
            causes.append(c)

        # Sort causes by strength (High > Medium > Low)
        # We assign numeric weights for sorting
        strength_weights = {
            RCAStrength.High: 3,
            RCAStrength.Medium: 2,
            RCAStrength.Low: 1,
        }
        causes.sort(key=lambda c: strength_weights[c.rca_strength], reverse=True)

        if not causes:
            causes.append(
                CandidateCause(
                    cause_type="unknown_cause",
                    rca_strength=RCAStrength.Low,
                    why_most_likely=["No specific diagnostic rules were triggered by the evidence."],
                )
            )

        return causes

    def _rule_db_unreachable(self, bundle: EvidenceBundle) -> CandidateCause:
        return CandidateCause(
            cause_type="db_unreachable",
            rca_strength=RCAStrength.High,
            why_most_likely=["All diagnostic queries returned UNAVAILABLE."],
            supporting_evidence_ids=[i.id for i in bundle.items],
        )

    def _rule_connection_saturation(self, bundle: EvidenceBundle) -> CandidateCause | None:
        active = bundle.get("active_connections")
        max_conn = bundle.get("max_connections")
        waiting = bundle.get("waiting_connections")

        if active is None or active.value is None or max_conn is None or max_conn.value is None:
            return None

        active_val = float(active.value)
        max_val = float(max_conn.value)
        if max_val == 0:
            return None

        saturation = active_val / max_val
        if saturation < 0.8:
            return None  # Rule doesn't fire

        waiting_val = float(waiting.value) if waiting and waiting.value is not None else 0.0

        if waiting_val > 0:
            strength = RCAStrength.High
            missing = []
        else:
            strength = RCAStrength.Medium
            missing = ["waiting_connections"]

        supporting_ids = [active.id, max_conn.id]
        if waiting:
            supporting_ids.append(waiting.id)

        return CandidateCause(
            cause_type="connection_saturation",
            rca_strength=strength,
            why_most_likely=[f"Active connections ({active_val}) are at {saturation:.1%} of max_connections ({max_val})."],
            supporting_evidence_ids=supporting_ids,
            missing_evidence=missing,
        )

    def _rule_slow_query_cpu_pressure(self, bundle: EvidenceBundle) -> CandidateCause | None:
        cpu = bundle.get("cpu_utilization")
        slow = bundle.get("slow_query_count")

        cpu_val = float(cpu.value) if cpu and cpu.value is not None else None
        slow_val = float(slow.value) if slow and slow.value is not None else None

        if cpu_val is None and slow_val is None:
            return None

        high_cpu = cpu_val is not None and cpu_val > 80.0
        high_slow = slow_val is not None and slow_val > 100.0

        if high_cpu and high_slow:
            return CandidateCause(
                cause_type="slow_query_cpu_pressure",
                rca_strength=RCAStrength.High,
                why_most_likely=[
                    f"CPU is high ({cpu_val}%) and slow query count is elevated ({slow_val})."
                ],
                supporting_evidence_ids=[i.id for i in [cpu, slow] if i],
            )

        if high_cpu:
            return CandidateCause(
                cause_type="slow_query_cpu_pressure",
                rca_strength=RCAStrength.Medium,
                why_most_likely=[f"CPU is high ({cpu_val}%)."],
                supporting_evidence_ids=[cpu.id],
                missing_evidence=["slow_query_count"],
            )

        if high_slow:
            return CandidateCause(
                cause_type="slow_query_cpu_pressure",
                rca_strength=RCAStrength.Medium,
                why_most_likely=[f"Slow query count is elevated ({slow_val})."],
                supporting_evidence_ids=[slow.id],
                missing_evidence=["cpu_utilization"],
            )

        return None

    def _rule_replication_lag(self, bundle: EvidenceBundle) -> CandidateCause | None:
        lag = bundle.get("replication_lag")
        lag_val = float(lag.value) if lag and lag.value is not None else None

        if lag_val is None or lag_val < 60.0:
            return None

        write_vol = bundle.get("write_volume")
        vol_val = float(write_vol.value) if write_vol and write_vol.value is not None else None

        if vol_val is not None and vol_val > 1000.0:
            strength = RCAStrength.High
            missing = []
        else:
            strength = RCAStrength.Medium
            missing = ["write_volume"]

        supporting_ids = [lag.id]
        if write_vol:
            supporting_ids.append(write_vol.id)

        return CandidateCause(
            cause_type="replication_lag",
            rca_strength=strength,
            why_most_likely=[f"Replication lag is elevated ({lag_val}s)."],
            supporting_evidence_ids=supporting_ids,
            missing_evidence=missing,
        )
