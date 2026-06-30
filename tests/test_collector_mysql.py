"""
Tests for the MySQL collector.
Unit tests mock aiomysql connections.
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from sentineldb.collectors.mysql import MySQLCollector
from sentineldb.core.enums import EvidenceStatus
from sentineldb.guardrails.catalog import MYSQL_CATALOG
from sentineldb.guardrails.checker import GuardrailChecker
from sentineldb.registry.models import InstanceConfig

_DEMO_INSTANCE = InstanceConfig(
    instance_id="mysql-demo-01",
    engine="mysql",
    host="localhost",
    port=3306,
    database="sentineldb",
    username="sentinel_ro",
    credential_ref="mysql_demo_ro",
)


@pytest.mark.asyncio
async def test_mysql_connection_failure_returns_all_unavailable() -> None:
    with patch("sentineldb.collectors.mysql.aiomysql.create_pool", side_effect=OSError("refused")):
        collector = MySQLCollector(_DEMO_INSTANCE)
        bundle = await collector.collect()

    assert bundle.instance_id == "mysql-demo-01"
    assert len(bundle.items) > 0
    assert all(item.status == EvidenceStatus.UNAVAILABLE for item in bundle.items)


@pytest.mark.asyncio
async def test_mysql_query_timeout_produces_unavailable_partial_result() -> None:
    mock_cur = AsyncMock()
    mock_cur.execute = AsyncMock()
    mock_cur.fetchone = AsyncMock(side_effect=asyncio.TimeoutError)

    class MockCursorCtx:
        async def __aenter__(self):
            return mock_cur
        async def __aexit__(self, exc_type, exc, tb):
            pass

    mock_conn = AsyncMock()
    mock_conn.cursor = MagicMock(return_value=MockCursorCtx())

    class MockAcquire:
        async def __aenter__(self):
            return mock_conn
        async def __aexit__(self, exc_type, exc, tb):
            pass

    mock_pool = MagicMock()
    mock_pool.acquire.return_value = MockAcquire()
    mock_pool.close = MagicMock()
    mock_pool.wait_closed = AsyncMock()

    with patch("sentineldb.collectors.mysql.aiomysql.create_pool", new_callable=AsyncMock, return_value=mock_pool):
        collector = MySQLCollector(_DEMO_INSTANCE)
        bundle = await collector.collect()

    assert len(bundle.items) > 0
    assert all(item.status == EvidenceStatus.UNAVAILABLE for item in bundle.items)


def test_mysql_all_catalog_queries_pass_guardrail_checker() -> None:
    checker = GuardrailChecker()
    for name, sql in MYSQL_CATALOG.items():
        result = checker.check(sql, engine="mysql")
        assert result.allowed, f"Catalog query '{name}' failed guardrail: {result.reason}"
