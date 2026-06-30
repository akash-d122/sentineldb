"""
Tests for the CloudWatch collector.
Unit tests mock boto3 clients.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from sentineldb.collectors.cloudwatch import CloudWatchCollector
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
    monitoring="cloudwatch",
)


@pytest.mark.asyncio
async def test_cloudwatch_happy_path() -> None:
    mock_client = MagicMock()
    mock_client.get_metric_statistics.return_value = {
        "Datapoints": [{"Timestamp": "2026-06-30T00:00:00Z", "Average": 45.5}]
    }

    with patch("sentineldb.collectors.cloudwatch.boto3.client", return_value=mock_client):
        collector = CloudWatchCollector(_DEMO_INSTANCE)
        bundle = await collector.collect()

    assert bundle.instance_id == "db-demo-01"
    assert len(bundle.items) == 7
    for item in bundle.items:
        assert item.status == EvidenceStatus.OK
        assert item.value == 45.5
        assert item.source == "cloudwatch"


@pytest.mark.asyncio
async def test_cloudwatch_missing_datapoints_returns_unavailable() -> None:
    mock_client = MagicMock()
    mock_client.get_metric_statistics.return_value = {"Datapoints": []}

    with patch("sentineldb.collectors.cloudwatch.boto3.client", return_value=mock_client):
        collector = CloudWatchCollector(_DEMO_INSTANCE)
        bundle = await collector.collect()

    assert len(bundle.items) == 7
    assert all(item.status == EvidenceStatus.UNAVAILABLE for item in bundle.items)


@pytest.mark.asyncio
async def test_cloudwatch_api_error_returns_unavailable() -> None:
    mock_client = MagicMock()
    mock_client.get_metric_statistics.side_effect = Exception("AWS Access Denied")

    with patch("sentineldb.collectors.cloudwatch.boto3.client", return_value=mock_client):
        collector = CloudWatchCollector(_DEMO_INSTANCE)
        bundle = await collector.collect()

    assert len(bundle.items) == 7
    assert all(item.status == EvidenceStatus.UNAVAILABLE for item in bundle.items)
