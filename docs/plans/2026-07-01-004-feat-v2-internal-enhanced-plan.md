---
title: "feat: V2 Internal Enhanced Version Plan"
type: feat
date: 2026-07-01
---

# V2 Internal Enhanced Version Implementation Plan

## Summary
Implement the V2 milestone for SentinelDB. This transitions the project from a local proof-of-life to an internal enhanced version suitable for broader team usage. It introduces enterprise authentication, extends monitoring capabilities with robust RDS/Aurora and Prometheus metrics, expands the safe diagnostic catalog, and begins laying the groundwork for a more interactive and configurable dashboard.

## Problem Frame
While V1 successfully proved the deterministic evidence-first pipeline locally, V2 needs to be resilient enough for internal production use. 
- The React dashboard is currently unprotected, which is unsafe for internal deployment.
- CloudWatch metrics are sparse, and Prometheus/PMM metrics were deferred entirely.
- The diagnostic catalog (which runs directly on the databases) lacks coverage for some of the most common DB issues: lock contention and long-running transactions.
- Integrations with ticketing systems like Freshdesk are missing.
- Users cannot configure alerting thresholds dynamically from the UI.

## Requirements
- **R1.** Integrate Auth0 / Supabase for enterprise-grade user authentication on the React dashboard and FastAPI backend.
- **R2.** Expand `MYSQL_CATALOG` and `POSTGRES_CATALOG` to include diagnostic queries for lock contention and long-running transactions, covered by guardrails.
- **R3.** Mature the RDS/Aurora CloudWatch collector by capturing comprehensive metrics (e.g., Read/Write IOPS, Freeable Memory, Replica Lag).
- **R4.** Implement a Prometheus/PMM collector to introduce specific historical baselines.
- **R5.** Introduce a Freshdesk integration for automated incident ticketing.
- **R6.** Introduce a Threshold UI allowing users to view and update baseline thresholds for instances.

## Key Technical Decisions
- **Auth Provider:** Supabase/Auth0 will be integrated using a standard OAuth2 / JWT bearer flow. FastAPI will validate the JWT signature, and React will manage the user session.
- **Collector Concurrency:** The CloudWatch and Prometheus collectors will continue to execute asynchronous API calls in parallel (via thread pools or native `asyncio`) to ensure the RCA process respects the < 60s SLA.
- **Catalog Safety:** The new lock contention and long-running transaction queries will be rigorously tested against the `sqlparse` guardrails to ensure they are strictly read-only (`SELECT`).

## Implementation Units

### U1. Diagnostic Catalog Expansion (Lock & Transaction)
- **Goal:** Expand DB diagnostic capabilities safely.
- **Requirements:** R2
- **Files:**
  - `src/sentineldb/guardrails/catalog.py`
  - `tests/test_catalog.py`
  - `tests/test_guardrails.py`
- **Approach:** Add read-only queries targeting `pg_locks`, `pg_stat_activity` (for Postgres) and `information_schema.innodb_trx` (for MySQL). Add them to the allowlist and verify guardrails block malicious variants but allow these.

### U2. RDS/Aurora Collector Maturity
- **Goal:** Expand CloudWatch metrics collected.
- **Requirements:** R3
- **Files:**
  - `src/sentineldb/collectors/cloudwatch.py`
  - `tests/test_collector_cloudwatch.py`
- **Approach:** Add `ReadIOPS`, `WriteIOPS`, `FreeableMemory`, `FreeStorageSpace`, and `AuroraReplicaLag` (if engine is Aurora) to the `_METRICS` mapping. Expand the mock tests to cover these points.

### U3. Prometheus/PMM Collector Implementation
- **Goal:** Enable baseline fetching from Prometheus/PMM.
- **Requirements:** R4
- **Files:**
  - `src/sentineldb/collectors/prometheus.py`
  - `tests/test_collector_prometheus.py`
  - `src/sentineldb/core/enums.py` (Add new evidence source enum)
- **Approach:** Use `httpx` to query Prometheus HTTP APIs asynchronously. Define a few standard PromQL queries representing historical load (e.g., 7-day average CPU) and include them in the `EvidenceBundle`.

### U4. Freshdesk Integration
- **Goal:** Send RCA reports to Freshdesk.
- **Requirements:** R5
- **Files:**
  - `src/sentineldb/notifications/freshdesk.py`
  - `src/sentineldb/worker/tasks.py`
  - `tests/test_notifications.py`
- **Approach:** Add a `FreshdeskNotifier` mimicking the structure of `JiraNotifier` and `SlackNotifier`. Wire it into the `_dispatch_notifications_async` flow.

### U5. Dashboard and API Authentication (Auth0/Supabase)
- **Goal:** Secure the V2 APIs and dashboard.
- **Requirements:** R1
- **Files:**
  - `src/sentineldb/api/dependencies.py` (New file for JWT auth)
  - `src/sentineldb/api/routes_incidents.py` (Protect endpoints)
  - `frontend/src/auth/` (React context for auth)
- **Approach:** Protect FastAPI routers using a `Depends(verify_jwt)` dependency. Configure the React app with the chosen provider's standard React SDK.

### U6. Threshold UI Configuration
- **Goal:** Allow users to update thresholds dynamically.
- **Requirements:** R6
- **Files:**
  - `src/sentineldb/api/routes_config.py` (New router)
  - `frontend/src/pages/ConfigPage.tsx`
- **Approach:** Move threshold definitions from hardcoded yaml/DB constants into an updatable table. Provide a standard CRUD UI in the React dashboard.

## Scope Boundaries
- **In-Scope:** Lock analysis, Prometheus metrics, Freshdesk integration, Auth validation, Threshold UI.
- **Deferred to V3:** Tenant isolation, billing, complex RBAC, onboarding flows, SaaS-level scalability.

## Verification
- Unit and integration tests must maintain 100% pass rate.
- Auth tokens must be explicitly required for all `/api/v1` routes (except a healthcheck).
- E2E tests should include the new lock contention queries and verify `sqlparse` correctly allows them.
