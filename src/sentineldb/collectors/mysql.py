"""
MySQL read-only evidence collector.

Executes only approved catalog queries via aiomysql.
Each query runs with a per-query timeout. Partial failures produce
UNAVAILABLE evidence items — no exception propagates to the caller.
"""

from __future__ import annotations

import asyncio
import os
from datetime import UTC, datetime

import aiomysql

from sentineldb.core.enums import EvidenceStatus
from sentineldb.core.models import EvidenceBundle, EvidenceItem
from sentineldb.guardrails.catalog import MYSQL_CATALOG
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


class MySQLCollector:
    """Read-only MySQL evidence collector using approved catalog queries."""

    def __init__(self, instance: InstanceConfig) -> None:
        self._instance = instance

    async def collect(self) -> EvidenceBundle:
        """Run all catalog queries concurrently and assemble an EvidenceBundle."""
        password = os.environ.get(self._instance.credential_ref, "password")
        try:
            pool = await aiomysql.create_pool(
                host=self._instance.host,
                port=self._instance.port,
                user=self._instance.username,
                password=password,
                db=self._instance.database,
                minsize=1,
                maxsize=5,
                autocommit=True,
            )
        except Exception:
            # All items UNAVAILABLE when connection fails
            items = [_unavailable(label, "aiomysql") for label in self._collectors()]
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
                    items.append(_unavailable(label, "aiomysql"))
            return EvidenceBundle(instance_id=self._instance.instance_id, items=items)
        finally:
            if pool:
                pool.close()
                await pool.wait_closed()

    async def _run_query(self, pool: aiomysql.Pool, label: str, sql: str) -> EvidenceItem:
        # Safety: every catalog query must pass the guardrail checker
        result = _CHECKER.check(sql, engine="mysql")
        if not result.allowed:
            return _unavailable(label, "guardrail_blocked")

        async with pool.acquire() as conn, conn.cursor() as cur:
            await cur.execute(sql)
            row = await cur.fetchone()

        if row is None:
            return _unavailable(label, "mysql")

        # Take the first column value
        value = row[0]
        numeric = float(value) if value is not None else None
        status = EvidenceStatus.OK if numeric is not None else EvidenceStatus.UNAVAILABLE

        return EvidenceItem(
            source="performance_schema" if "slow" in label else "mysql",
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
        return {k: MYSQL_CATALOG[k] for k in keys if k in MYSQL_CATALOG}
