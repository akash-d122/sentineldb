"""
PostgreSQL read-only evidence collector.

Executes only approved catalog queries via asyncpg.
Each query runs with a per-query timeout. Partial failures produce
UNAVAILABLE evidence items — no exception propagates to the caller.
"""

from __future__ import annotations

import asyncio
import os
from datetime import UTC, datetime

import asyncpg

from sentineldb.core.enums import EvidenceStatus
from sentineldb.core.models import EvidenceBundle, EvidenceItem
from sentineldb.guardrails.catalog import POSTGRES_CATALOG
from sentineldb.guardrails.checker import GuardrailChecker
from sentineldb.registry.models import InstanceConfig

_CHECKER = GuardrailChecker()
_QUERY_TIMEOUT = 10.0  # seconds per query


def _unavailable(label: str, source: str) -> EvidenceItem:
    return EvidenceItem(
        source=source,
        label=label,
        value=None,
        status=EvidenceStatus.UNAVAILABLE,
        display_text=f"{label}: UNAVAILABLE",
    )


class PostgresCollector:
    """Read-only PostgreSQL evidence collector using approved catalog queries."""

    def __init__(self, instance: InstanceConfig) -> None:
        self._instance = instance

    async def collect(self) -> EvidenceBundle:
        """Run all catalog queries concurrently and assemble an EvidenceBundle."""
        dsn = self._build_dsn()
        try:
            pool = await asyncpg.create_pool(dsn, min_size=1, max_size=5)
        except Exception:
            # All items UNAVAILABLE when connection fails
            items = [_unavailable(label, "asyncpg") for label in self._collectors()]
            return EvidenceBundle(instance_id=self._instance.instance_id, items=items)

        try:
            tasks = {
                label: asyncio.create_task(
                    asyncio.wait_for(self._run_query(pool, label, sql), timeout=_QUERY_TIMEOUT)
                )
                for label, sql in self._collectors().items()
            }
            results = await asyncio.gather(*tasks.values(), return_exceptions=True)
            items: list[EvidenceItem] = []
            for label, result in zip(tasks.keys(), results, strict=True):
                if isinstance(result, EvidenceItem):
                    items.append(result)
                else:
                    items.append(_unavailable(label, "asyncpg"))
            return EvidenceBundle(instance_id=self._instance.instance_id, items=items)
        finally:
            if pool:
                await pool.close()

    async def _run_query(self, pool: asyncpg.Pool, label: str, sql: str) -> EvidenceItem:
        # Safety: every catalog query must pass the guardrail checker
        result = _CHECKER.check(sql)
        if not result.allowed:
            return _unavailable(label, "guardrail_blocked")

        async with pool.acquire() as conn:
            row = await conn.fetchrow(sql)
        if row is None:
            return _unavailable(label, "pg")

        # Take the first column value
        value = row[0]
        numeric = float(value) if value is not None else None
        status = EvidenceStatus.OK if numeric is not None else EvidenceStatus.UNAVAILABLE

        return EvidenceItem(
            source="pg_stat_activity" if "activity" in label else "pg",
            label=label,
            value=numeric,
            timestamp=datetime.now(UTC),
            status=status,
            display_text=f"{label}: {numeric}",
        )

    def _collectors(self) -> dict[str, str]:
        """Return the subset of catalog queries used by this collector."""
        keys = [
            "active_connections",
            "waiting_connections",
            "replication_lag",
            "db_size",
            "slow_query_count",
            "lock_contention",
            "long_running_transactions",
        ]
        return {k: POSTGRES_CATALOG[k] for k in keys if k in POSTGRES_CATALOG}

    def _build_dsn(self) -> str:
        """Build asyncpg DSN from InstanceConfig + env credential."""
        password = os.environ.get(self._instance.credential_ref, "password")
        return (
            f"postgresql://{self._instance.username}:{password}"
            f"@{self._instance.host}:{self._instance.port}/{self._instance.database}"
        )
