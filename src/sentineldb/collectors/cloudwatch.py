"""
AWS CloudWatch metrics collector.

Uses boto3 to fetch infrastructure metrics. Boto3 is synchronous,
so network calls are wrapped in asyncio.to_thread to avoid blocking
the Celery worker's event loop.
"""

from __future__ import annotations

import asyncio
import os
import time
from datetime import UTC, datetime, timedelta

import boto3

from sentineldb.core.enums import EvidenceStatus
from sentineldb.core.models import EvidenceBundle, EvidenceItem
from sentineldb.registry.models import InstanceConfig

# We will collect standard metrics from the AWS/RDS namespace
_METRICS = {
    "cloudwatch_cpu": "CPUUtilization",
    "cloudwatch_connections": "DatabaseConnections",
    "cloudwatch_read_iops": "ReadIOPS",
    "cloudwatch_write_iops": "WriteIOPS",
    "cloudwatch_freeable_memory": "FreeableMemory",
    "cloudwatch_free_storage_space": "FreeStorageSpace",
    "cloudwatch_aurora_replica_lag": "AuroraReplicaLag",
}


# R5: 60s TTL Cache to prevent aggressive API spikes during active RCA viewing
_cache: dict[str, tuple[float, EvidenceItem]] = {}
CACHE_TTL = 60.0


class CloudWatchCollector:
    """Evidence collector for AWS CloudWatch metrics."""

    def __init__(self, instance: InstanceConfig) -> None:
        self._instance = instance
        # Identify the DBInstanceIdentifier from config (assume it matches instance_id for now)
        self._db_identifier = self._instance.instance_id

    async def collect(self) -> EvidenceBundle:
        """Fetch all configured metrics concurrently via threads."""
        try:
            # We defer client creation so it runs in the thread (boto3 is not perfectly thread-safe
            # when sharing session/clients across threads if not careful, but creating per call is safe).
            # For simplicity, we just use the default session.
            tasks = {
                label: asyncio.to_thread(self._fetch_metric, metric_name, label)
                for label, metric_name in _METRICS.items()
            }
            results = await asyncio.gather(*tasks.values(), return_exceptions=True)

            items: list[EvidenceItem] = []
            for label, result in zip(tasks.keys(), results, strict=True):
                if isinstance(result, EvidenceItem):
                    items.append(result)
                else:
                    items.append(EvidenceItem.unavailable("cloudwatch", label))
            return EvidenceBundle(instance_id=self._instance.instance_id, items=items)
        except Exception:
            items = [EvidenceItem.unavailable("cloudwatch", label) for label in _METRICS]
            return EvidenceBundle(instance_id=self._instance.instance_id, items=items)

    def _fetch_metric(self, metric_name: str, label: str) -> EvidenceItem:
        """Fetch a single metric statistic from CloudWatch."""
        cache_key = f"{self._db_identifier}:{metric_name}"
        cached = _cache.get(cache_key)
        if cached and time.time() - cached[0] < CACHE_TTL:
            return cached[1]

        region = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")

        client = boto3.client("cloudwatch", region_name=region)

        now = datetime.now(UTC)
        start_time = now - timedelta(minutes=5)

        try:
            response = client.get_metric_statistics(
                Namespace="AWS/RDS",
                MetricName=metric_name,
                Dimensions=[{"Name": "DBInstanceIdentifier", "Value": self._db_identifier}],
                StartTime=start_time,
                EndTime=now,
                Period=300,
                Statistics=["Average"],
            )
            datapoints = response.get("Datapoints", [])
            if not datapoints:
                return EvidenceItem.unavailable("cloudwatch", label)

            # Take the most recent datapoint
            latest = sorted(datapoints, key=lambda x: x["Timestamp"], reverse=True)[0]
            value = latest["Average"]

            item = EvidenceItem(
                source="cloudwatch",
                label=label,
                value=value,
                timestamp=now,
                status=EvidenceStatus.OK,
                display_text=f"{label}: {value:.2f}",
            )
            _cache[cache_key] = (time.time(), item)
            return item
        except Exception:
            return EvidenceItem.unavailable("cloudwatch", label)
