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

# We dynamically build the queries based on engine (postgres vs mysql)
_BASE_QUERIES = {
    "cpu": 'avg_over_time(node_cpu_seconds_total{{mode!="idle", {labels}}}[{window}]{offset})',
    "connections_pg": "avg_over_time(pg_stat_activity_count{{{labels}}}[{window}]{offset})",
    "connections_mysql": "avg_over_time(mysql_global_status_threads_connected{{{labels}}}[{window}]{offset})",
    "qps_mysql": "rate(mysql_global_status_questions{{{labels}}}[{window}]{offset})",
    "qps_pg": "rate(pg_stat_database_xact_commit{{{labels}}}[{window}]{offset})",
}

_TIMEFRAMES = {
    "1h": {"window": "1h", "offset": ""},
    "1d_ago": {"window": "1h", "offset": " offset 1d"},
    "7d_ago": {"window": "1h", "offset": " offset 7d"},
}


class PrometheusCollector:
    """Evidence collector for Prometheus metrics (e.g., historical baselines)."""

    def __init__(self, instance: InstanceConfig) -> None:
        self._instance = instance

        # Build prometheus label selectors
        if self._instance.monitoring and self._instance.monitoring.pmm_service_name:
            self._labels = f'service_name="{self._instance.monitoring.pmm_service_name}"'
        elif self._instance.monitoring and self._instance.monitoring.job_name:
            self._labels = f'job="{self._instance.monitoring.job_name}", instance="{self._instance.host}:{self._instance.port}"'
        else:
            self._labels = f'instance="{self._instance.host}:{self._instance.port}"'

        # Fetch prometheus URL from config or env
        if self._instance.monitoring and self._instance.monitoring.url:
            self._prom_url = self._instance.monitoring.url
        else:
            self._prom_url = os.environ.get("PROMETHEUS_URL", "http://localhost:9090")

        # Select active metric types based on engine
        self._active_metrics = ["cpu"]
        if self._instance.engine == "postgresql":
            self._active_metrics.extend(["connections_pg", "qps_pg"])
        else:
            self._active_metrics.extend(["connections_mysql", "qps_mysql"])

    def _build_queries(self) -> dict[str, str]:
        queries = {}
        for metric in self._active_metrics:
            template = _BASE_QUERIES[metric]
            for tf_name, tf_kwargs in _TIMEFRAMES.items():
                label = f"prom_{metric}_{tf_name}"
                queries[label] = template.format(labels=self._labels, **tf_kwargs)
        return queries

    async def collect(self) -> EvidenceBundle:
        """Fetch all configured metrics concurrently."""
        queries = self._build_queries()
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                tasks = {
                    label: self._fetch_metric(client, query, label)
                    for label, query in queries.items()
                }
                results = await asyncio.gather(*tasks.values(), return_exceptions=True)

                items: list[EvidenceItem] = []
                for label, result in zip(tasks.keys(), results, strict=True):
                    if isinstance(result, EvidenceItem):
                        items.append(result)
                    else:
                        items.append(EvidenceItem.unavailable("prometheus", label))
                return EvidenceBundle(instance_id=self._instance.instance_id, items=items)
        except Exception:
            items = [EvidenceItem.unavailable("prometheus", label) for label in queries]
            return EvidenceBundle(instance_id=self._instance.instance_id, items=items)

    async def _fetch_metric(
        self, client: httpx.AsyncClient, query: str, label: str
    ) -> EvidenceItem:
        """Fetch a single metric statistic via PromQL."""
        try:
            response = await client.get(
                f"{self._prom_url}/api/v1/query",
                params={"query": query},
            )
            response.raise_for_status()
            data = response.json()

            if data.get("status") != "success":
                return EvidenceItem.unavailable("prometheus", label)

            results = data.get("data", {}).get("result", [])
            if not results:
                return EvidenceItem.unavailable("prometheus", label)

            value_str = results[0].get("value", [None, None])[1]
            if value_str is None:
                return EvidenceItem.unavailable("prometheus", label)

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
            return EvidenceItem.unavailable("prometheus", label)
