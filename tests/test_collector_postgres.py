"""
Tests for the PostgreSQL collector.

Unit tests mock asyncpg connections.
Integration tests require Docker Compose (`docker compose up -d db`).
Skip integration tests by default: set DOCKER_INTEGRATION=1 to run them.
"""

from __future__ import annotations

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from sentineldb.collectors.postgres import PostgresCollector
from sentineldb.core.enums import EvidenceStatus
from sentineldb.guardrails.catalog import POSTGRES_CATALOG
from sentineldb.guardrails.checker import GuardrailChecker
from sentineldb.registry.models import InstanceConfig

_DEMO_INSTANCE = InstanceConfig(
    instance_id="db-demo-01",
    engine="postgresql",
    host="localhost",
    port=5432,
    database="sentineldb",
    username="sentinel_ro",
    credential_ref="pg_demo_ro",
)

integration = pytest.mark.skipif(
    os.environ.get("DOCKER_INTEGRATION") != "1",
    reason="Requires Docker Compose db service (DOCKER_INTEGRATION=1)",
)


# ---------------------------------------------------------------------------
# Unit tests — mocked asyncpg
# ---------------------------------------------------------------------------


def _make_row(value: float) -> MagicMock:
    row = MagicMock()
    row.__getitem__ = MagicMock(return_value=value)
    return row


@pytest.mark.asyncio
async def test_connection_failure_returns_all_unavailable() -> None:
    with patch(
        "sentineldb.collectors.postgres.asyncpg.create_pool", side_effect=OSError("refused")
    ):
        collector = PostgresCollector(_DEMO_INSTANCE)
        bundle = await collector.collect()

    assert bundle.instance_id == "db-demo-01"
    assert len(bundle.items) > 0
    assert all(item.status == EvidenceStatus.UNAVAILABLE for item in bundle.items)


@pytest.mark.asyncio
async def test_query_timeout_produces_unavailable_partial_result() -> None:
    import asyncio

    mock_conn = AsyncMock()
    mock_conn.fetchrow = AsyncMock(side_effect=asyncio.TimeoutError)

    class MockAcquire:
        async def __aenter__(self):
            return mock_conn

        async def __aexit__(self, exc_type, exc, tb):
            pass

    mock_pool = MagicMock()
    mock_pool.acquire.return_value = MockAcquire()
    mock_pool.close = AsyncMock()

    with patch(
        "sentineldb.collectors.postgres.asyncpg.create_pool",
        new_callable=AsyncMock,
        return_value=mock_pool,
    ):
        collector = PostgresCollector(_DEMO_INSTANCE)
        bundle = await collector.collect()

    assert len(bundle.items) > 0
    assert all(item.status == EvidenceStatus.UNAVAILABLE for item in bundle.items)


@pytest.mark.asyncio
async def test_pg_stat_statements_unavailable_returns_unavailable_item() -> None:
    """When pg_stat_statements is not installed, slow_query_count is UNAVAILABLE."""

    async def mock_fetchrow(sql: str) -> list[float] | None:
        if "pg_stat_statements" in sql:
            raise Exception("relation does not exist")
        return [10.0]

    mock_conn = AsyncMock()
    mock_conn.fetchrow = mock_fetchrow

    class MockAcquire:
        async def __aenter__(self):
            return mock_conn

        async def __aexit__(self, exc_type, exc, tb):
            pass

    mock_pool = MagicMock()
    mock_pool.acquire.return_value = MockAcquire()
    mock_pool.close = AsyncMock()

    with patch(
        "sentineldb.collectors.postgres.asyncpg.create_pool",
        new_callable=AsyncMock,
        return_value=mock_pool,
    ):
        collector = PostgresCollector(_DEMO_INSTANCE)
        bundle = await collector.collect()

    slow_query = bundle.get("slow_query_count")
    assert slow_query is not None
    assert slow_query.status == EvidenceStatus.UNAVAILABLE

    # Other items should still have values
    active = bundle.get("active_connections")
    assert active is not None
    assert active.status == EvidenceStatus.OK


def test_all_catalog_queries_pass_guardrail_checker() -> None:
    """All queries used by the collector must be in the approved catalog."""
    checker = GuardrailChecker()
    for name, sql in POSTGRES_CATALOG.items():
        result = checker.check(sql, engine="postgresql")
        assert result.allowed, f"Catalog query '{name}' failed guardrail: {result.reason}"


def test_evidence_items_have_required_fields() -> None:
    """EvidenceItem schema: source, label, display_text must be non-empty."""
    from sentineldb.core.enums import EvidenceStatus
    from sentineldb.core.models import EvidenceItem

    item = EvidenceItem(
        source="pg",
        label="active_connections",
        value=42.0,
        status=EvidenceStatus.OK,
        display_text="active_connections: 42.0",
    )
    assert item.source
    assert item.label
    assert item.display_text


# ---------------------------------------------------------------------------
# Integration tests — require Docker Compose db service
# ---------------------------------------------------------------------------


@integration
@pytest.mark.asyncio
async def test_integration_collector_returns_evidence_from_docker_pg() -> None:
    from sentineldb.registry.loader import InstanceRegistry

    # Mock registry host to localhost since this runs on the host outside docker
    original_resolve = InstanceRegistry.resolve

    def mocked_resolve(self, instance_id: str):
        instance = original_resolve(self, instance_id)
        if instance.host == "db":
            return instance.model_copy(update={"host": "127.0.0.1", "port": 5433})
        return instance

    with patch(
        "sentineldb.registry.loader.InstanceRegistry.resolve",
        side_effect=mocked_resolve,
        autospec=True,
    ):
        reg = InstanceRegistry("instances.yaml")
        instance = reg.resolve("db-demo-01")
    collector = PostgresCollector(instance)
    bundle = await collector.collect()

    non_unavailable = [i for i in bundle.items if i.status != EvidenceStatus.UNAVAILABLE]
    assert len(non_unavailable) >= 3, (
        f"Expected >=3 non-UNAVAILABLE items, got {len(non_unavailable)}: "
        + str([i.label for i in bundle.items])
    )
    for item in bundle.items:
        assert item.source
        assert item.label
        assert item.display_text
