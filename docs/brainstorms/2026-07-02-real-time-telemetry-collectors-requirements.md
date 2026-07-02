---
date: 2026-07-02
topic: real-time-telemetry-collectors
---

# Real-Time Telemetry & Collectors Requirements

## Summary
Upgrading the SentinelDB incident pipeline to support real-time data flow. This involves replacing the current mocked data collectors with actual CloudWatch and Prometheus integrations, and establishing a Server-Sent Events (SSE) streaming architecture to broadcast live incident updates from the FastAPI backend to the Next.js frontend.

## Problem Frame
The current V3 MVP successfully isolates tenants and processes incidents asynchronously via Celery, but the dashboard requires manual refreshes to see new incidents. Additionally, the metric evidence relies on stubbed local data. To provide true diagnostic value during high-stress database outages, Database Engineers (DBEs) need a live stream of incoming alerts and real telemetry evidence pulled directly from their production monitoring systems.

## Key Decisions

**Server-Sent Events (SSE) for Live Feed**
Using SSE for the live incident feed rather than WebSockets. Since the feed is a uni-directional (server-to-client) broadcast, SSE simplifies load balancing, minimizes connection overhead, and natively leverages standard HTTP semantics.

**Redis Pub/Sub State Sync**
The background Celery workers will publish incident state changes to a Redis PubSub channel. The FastAPI SSE endpoint will subscribe to this channel and fan out updates to connected clients based on their tenant ID.

## Requirements

**Streaming & Architecture**
- R1. The FastAPI backend must expose an SSE endpoint (e.g., `/api/v1/incidents/stream`) that broadcasts incident status changes to authenticated tenants.
- R2. The Next.js frontend must consume the SSE stream and optimistically update the Incident Feed without requiring a full page reload.
- R3. The background worker must publish incident state changes to a Redis PubSub channel that the FastAPI layer subscribes to.
- R4. FastAPI must fetch and emit the latest incident state upon initial SSE connection establishment to reconcile any missed PubSub events during client disconnection.

**Data Collectors**
- R5. The system must implement a real `CloudWatchCollector` capable of fetching CPU, IOPS, and DB connections using AWS `boto3`.
- R6. The system must implement a real `PrometheusCollector` capable of executing PromQL queries against a specified Prometheus or PMM endpoint.
- R7. Both collectors must conform to the existing internal evidence contract and return deterministic `EvidenceItem` structures.

## Scope Boundaries

- **Deferred to Follow-Up Work:** Interactive real-time chart zooming (static snapshot charts or basic sparklines are acceptable for now), dynamic AWS IAM cross-account role assumption (we will rely on static environment keys or local IAM profiles for V1).
- **API Cost Protection:** CloudWatch and Prometheus queries must implement a minimum polling interval (e.g., 30s-60s) or caching layer to prevent API rate-limiting and aggressive cost spikes during active viewing.
- **Outside this product's identity:** Building a full-fledged metrics storage engine or time-series database. SentinelDB only queries and caches evidence specific to the active RCA window.

## Outstanding Questions

- **Deferred to Planning (Auth):** How will the Next.js frontend securely negotiate the SSE connection with the FastAPI backend? Standard `EventSource` APIs do not support passing `Authorization` headers natively. Consider evaluating `@microsoft/fetch-event-source` (which supports custom headers) or a secure Next.js Server Component proxy to avoid URL-based tokens entirely.
- **Deferred to Planning (PromQL):** Determine whether the Prometheus collector relies on instant queries (single snapshot) or range queries (timeseries data) to standardize the JSON parsing logic, as they return fundamentally different data shapes.