"""
RCA Output Renderer.

Produces the final IncidentReport from the selected CandidateCause, EvidenceBundle,
and optional RunbookMatch. This is the deterministic output path.
"""

from __future__ import annotations

from sentineldb.core.models import (
    AlertPayload,
    CandidateCause,
    EvidenceBundle,
    IncidentReport,
    RunbookMatch,
    SafeAction,
)


class Renderer:
    """Renders an EvidenceBundle and CandidateCause into an IncidentReport."""

    def render(
        self,
        incident_id: str,
        alert: AlertPayload,
        cause: CandidateCause,
        bundle: EvidenceBundle,
        runbook: RunbookMatch | None,
    ) -> IncidentReport:
        """Render the complete IncidentReport (deterministic path)."""

        return IncidentReport(
            incident_id=incident_id,
            rca_strength=cause.rca_strength,
            root_cause_summary=self._template_summary(cause, bundle),
            why_most_likely=cause.why_most_likely,
            evidence=bundle.items,  # Pass through exactly as collected
            runbook_reference=runbook,
            safe_next_actions=self._safe_actions_for(cause.cause_type),
            requires_approval=self._requires_approval_for(cause.cause_type),
            missing_evidence=cause.missing_evidence,
            llm_used=False,
        )

    def _template_summary(self, cause: CandidateCause, bundle: EvidenceBundle) -> str:
        """Generate a deterministic root cause summary string."""
        if cause.cause_type == "connection_saturation":
            active = bundle.get("active_connections")
            active_val = active.value if active else "unknown"
            return f"Database connection pool saturation: {active_val} active connections."

        if cause.cause_type == "slow_query_cpu_pressure":
            return "CPU pressure driven by a spike in slow query execution."

        if cause.cause_type == "replication_lag":
            return "Elevated replication lag on read replica."

        if cause.cause_type == "db_unreachable":
            return "Database instance is unreachable (all diagnostic queries failed)."

        return "Unknown root cause; diagnostic rules did not match the current evidence."

    def _safe_actions_for(self, cause_type: str) -> list[SafeAction]:
        """Return approved SafeActions for the given cause type."""
        base_actions = [
            SafeAction(
                label="Check active connections",
                description="View currently executing queries.",
                catalog_key="active_connections",
            )
        ]

        if cause_type == "connection_saturation":
            return base_actions + [
                SafeAction(
                    label="Check waiting connections",
                    description="View lock-blocked sessions.",
                    catalog_key="waiting_connections",
                )
            ]

        if cause_type == "slow_query_cpu_pressure":
            return base_actions + [
                SafeAction(
                    label="Check top slow queries",
                    description="View top queries by execution time.",
                    catalog_key="slow_query_count",
                )
            ]

        if cause_type == "replication_lag":
            return [
                SafeAction(
                    label="Check replication lag",
                    description="View current lag in seconds.",
                    catalog_key="replication_lag",
                )
            ]

        return base_actions

    def _requires_approval_for(self, cause_type: str) -> list[str]:
        """Return risky actions that require DBE approval."""
        if cause_type == "connection_saturation":
            return ["Killing sessions (pg_terminate_backend)", "Increasing max_connections"]

        if cause_type == "slow_query_cpu_pressure":
            return ["Killing long-running queries", "Adding/modifying indexes"]

        if cause_type == "db_unreachable":
            return ["Restarting DB service", "Failover"]

        if cause_type == "replication_lag":
            return ["Replica restart", "Failover"]

        return []
