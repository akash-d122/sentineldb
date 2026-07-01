"""
Tests for the Prometheus collector.
Unit tests mock httpx client.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from sentineldb.collectors.prometheus import PrometheusCollector
from sentineldb.core.enums import EvidenceStatus
from sentineldb.registry.models import InstanceConfig

_DEMO_INSTANCE = InstanceConfig(
    instance_id="db-demo-01",
    engine="postgresql",
    host="localhost",
    port=5432,
    database="sentineldb",
    username="sentinel_ro",
    credential_ref="pg_demo_ro",
    monitoring="prometheus",
)


@pytest.mark.asyncio
async def test_prometheus_happy_path() -> None:
    mock_response = AsyncMock()
    mock_response.json = lambda: {
        "status": "success",
        "data": {
            "resultType": "vector",
            "result": [{"metric": {}, "value": [1700000000.0, "45.5"]}],
        },
    }
    mock_response.raise_for_status = lambda: None

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.get = AsyncMock(return_value=mock_response)

    with patch("sentineldb.collectors.prometheus.httpx.AsyncClient", return_value=mock_client):
        collector = PrometheusCollector(_DEMO_INSTANCE)
        bundle = await collector.collect()

    assert bundle.instance_id == "db-demo-01"
    assert len(bundle.items) == 3
    for item in bundle.items:
        assert item.status == EvidenceStatus.OK
        assert item.value == 45.5
        assert item.source == "prometheus"


@pytest.mark.asyncio
async def test_prometheus_missing_results_returns_unavailable() -> None:
    mock_response = AsyncMock()
    mock_response.json = lambda: {
        "status": "success",
        "data": {"resultType": "vector", "result": []},
    }
    mock_response.raise_for_status = lambda: None

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.get = AsyncMock(return_value=mock_response)

    with patch("sentineldb.collectors.prometheus.httpx.AsyncClient", return_value=mock_client):
        collector = PrometheusCollector(_DEMO_INSTANCE)
        bundle = await collector.collect()

    assert len(bundle.items) == 3
    assert all(item.status == EvidenceStatus.UNAVAILABLE for item in bundle.items)


@pytest.mark.asyncio
async def test_prometheus_api_error_returns_unavailable() -> None:
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.get.side_effect = httpx.RequestError("Connection failed")

    with patch("sentineldb.collectors.prometheus.httpx.AsyncClient", return_value=mock_client):
        collector = PrometheusCollector(_DEMO_INSTANCE)
        bundle = await collector.collect()

    assert len(bundle.items) == 3
    assert all(item.status == EvidenceStatus.UNAVAILABLE for item in bundle.items)
