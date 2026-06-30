"""
Prometheus/PMM metrics collector.

Uses httpx to fetch historical baselines via PromQL asynchronously.
"""

from __future__ import annotations

import asyncio
import os
from datetime import UTC, datetime

import httpx

from sentineldb.core.enums import EvidenceStatus
from sentineldb.core.models import EvidenceBundle, EvidenceItem
from sentineldb.registry.models import InstanceConfig

_METRICS = {
    "prom_7d_avg_cpu": 'avg_over_time(node_cpu_seconds_total{mode!="idle", instance="{instance}"}[7d])',
    "prom_7d_avg_connections": 'avg_over_time(pg_stat_activity_count{instance="{instance}"}[7d])',
    "prom_7d_avg_qps": 'avg_over_time(mysql_global_status_questions{instance="{instance}"}[7d])',
}

def _unavailable(label: str) -> EvidenceItem:
    return EvidenceItem(
        source="prometheus",
        label=label,
        value=None,
        status=EvidenceStatus.UNAVAILABLE,
        display_text=f"{label}: UNAVAILABLE",
    )

class PrometheusCollector:
    """Evidence collector for Prometheus metrics (e.g., historical baselines)."""

    def __init__(self, instance: InstanceConfig) -> None:
        self._instance = instance
        # Identify the prometheus instance label (often matches host:port or instance_id)
        self._prom_instance = f"{self._instance.host}:{self._instance.port}"
        # Fetch prometheus URL from env, default to local if not set
        self._prom_url = os.environ.get("PROMETHEUS_URL", "http://localhost:9090")

    async def collect(self) -> EvidenceBundle:
        """Fetch all configured metrics concurrently."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                tasks = {
                    label: self._fetch_metric(client, query_template, label)
                    for label, query_template in _METRICS.items()
                }
                results = await asyncio.gather(*tasks.values(), return_exceptions=True)

                items: list[EvidenceItem] = []
                for label, result in zip(tasks.keys(), results, strict=True):
                    if isinstance(result, EvidenceItem):
                        items.append(result)
                    else:
                        items.append(_unavailable(label))
                return EvidenceBundle(instance_id=self._instance.instance_id, items=items)
        except Exception:
            items = [_unavailable(label) for label in _METRICS]
            return EvidenceBundle(instance_id=self._instance.instance_id, items=items)

    async def _fetch_metric(self, client: httpx.AsyncClient, query_template: str, label: str) -> EvidenceItem:
        """Fetch a single metric statistic via PromQL."""
        query = query_template.replace("{instance}", self._prom_instance)
        try:
            response = await client.get(
                f"{self._prom_url}/api/v1/query",
                params={"query": query},
            )
            response.raise_for_status()
            data = response.json()

            if data.get("status") != "success":
                return _unavailable(label)

            results = data.get("data", {}).get("result", [])
            if not results:
                return _unavailable(label)

            # Take the value from the first result vector
            # value is typically [timestamp, "string_value"]
            value_str = results[0].get("value", [None, None])[1]
            if value_str is None:
                return _unavailable(label)

            value = float(value_str)

            return EvidenceItem(
                source="prometheus",
                label=label,
                value=value,
                timestamp=datetime.now(UTC),
                status=EvidenceStatus.OK,
                display_text=f"{label}: {value:.2f}",
            )
        except Exception:
            return _unavailable(label)
