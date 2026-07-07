---
title: "feat: Expand Collector Coverage (PMM / Prometheus)"
type: feat
date: 2026-07-07
---

# PMM / Prometheus Collector Expansion Plan

## Summary
Expand the Prometheus/PMM collector to fetch structured historical baselines (1h, 1d, 7d) as defined in the PRD, and update the `InstanceConfig` registry model to support detailed monitoring configuration instead of a flat string.

## Requirements
- **R1:** Update `InstanceConfig` in `src/sentineldb/registry/models.py` to support a `MonitoringConfig` object (e.g., `provider`, `job_name`, `pmm_service_name`).
- **R2:** Update `instances.yaml` to include a sample Prometheus configuration.
- **R3:** Expand `PrometheusCollector` to fetch three historical baselines for key metrics (CPU, Connections):
  - Current window (last 1h avg)
  - Previous day (avg over 1h, offset 1d)
  - Previous week (avg over 1h, offset 7d)
- **R4:** Ensure backward compatibility with existing tests by updating `test_collector_prometheus.py` and other dependent tests.

## Technical Decisions
- **PromQL Offset Modifier:** Use Prometheus `offset` syntax (`avg_over_time(metric[1h] offset 1d)`) to efficiently fetch historical baselines in a single API round-trip per timeframe.
- **Graceful Degradation:** If Prometheus is unreachable, the collector returns `EvidenceStatus.UNAVAILABLE` items, ensuring the RCA pipeline can still generate a fallback report without crashing.

## Implementation Units
- **U1:** Refactor `registry/models.py` to introduce `MonitoringConfig`.
- **U2:** Update `PrometheusCollector` with the new PromQL queries and `offset` syntax.
- **U3:** Update tests to mock the new expanded queries.
