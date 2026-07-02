---
date: 2026-07-02
type: feat
origin: docs/brainstorms/2026-07-02-real-time-telemetry-collectors-requirements.md
---

# Real-Time Telemetry & Collectors Plan

**Target repo:** `.`

## Summary
Upgrade SentinelDB V3 to push real-time incident updates from the FastAPI backend to the Next.js frontend using Server-Sent Events (SSE). It also enhances the existing CloudWatch and Prometheus collectors with an API cost-protection caching layer.

## Problem Frame
Currently, incident status updates require manual browser refreshes, and the UI lacks real-time awareness of RCA pipeline progression. Additionally, fetching real-time telemetry from AWS CloudWatch or Prometheus repeatedly during an active incident poses a significant API cost and rate-limiting risk. This plan establishes an SSE streaming architecture powered by Redis PubSub, and implements a caching safety net for telemetry fetching.

## Requirements
- R1. Expose an SSE endpoint (`/api/v1/incidents/stream`) to broadcast incident status.
- R2. Next.js frontend consumes SSE securely to bypass browser `Authorization` header limitations.
- R3. Celery background workers publish state changes (queued, report_ready, failed) to a Redis PubSub channel.
- R4. FastAPI must fetch and emit the latest state upon SSE connection.
- R5. Add a 60s TTL cache to `CloudWatchCollector` and `PrometheusCollector` to prevent aggressive API spikes.
- R6. Ensure PromQL logic explicitly handles the required query type (standardizing on instant queries).

## Key Technical Decisions
- **Next.js API Route Proxy for SSE:** We will implement an API route inside Next.js (`frontend/src/app/api/stream/route.ts`) that extracts the JWT from the Supabase session cookie and forwards the SSE stream from FastAPI. This bypasses the browser `EventSource` header limitation securely.
- **Redis.asyncio for PubSub:** We will utilize the existing `redis` package and `settings.REDIS_URL` to create an async pubsub client inside FastAPI and Celery.
- **In-Memory TTL Cache:** We will implement a lightweight, thread-safe in-memory cache dictionary with timestamp invalidation to wrap the AWS/Prometheus collector queries within the FastAPI process.

---

### U1. Redis PubSub Event Publishing
**Goal:** Instrument Celery and FastAPI incident creation logic to publish state updates to Redis.
**Files:**
- `src/sentineldb/services/incident.py`
- `src/sentineldb/worker/tasks.py`
**Approach:**
- Instantiate an async Redis client using `redis.asyncio.from_url(settings.REDIS_URL)`.
- Publish `{"incident_id": "...", "status": "queued", "tenant_id": "..."}` in `create_and_analyze_incident`.
- Publish `report_ready` inside `_analyze` and `failed` inside `_mark_failed`.
- Publish to channel `incident_updates:{tenant_id}`.
**Test scenarios:**
- Covers happy path: Creating an incident publishes a "queued" event.
- Covers integration: Finishing an analysis publishes "report_ready".

### U2. FastAPI SSE Stream Endpoint
**Goal:** Create the `/api/v1/incidents/stream` route to fan out Redis PubSub messages to connected clients.
**Files:**
- `src/sentineldb/api/routes_stream.py`
- `src/sentineldb/api/main.py`
**Approach:**
- Use FastAPI `StreamingResponse`.
- Inside the generator, query the DB for the current status of recent incidents to satisfy R4 (fetch latest state upon connect). Yield this initial state.
- Subscribe to the Redis PubSub channel `incident_updates:{tenant_id}`.
- Yield events as they arrive (`yield f"data: {json.dumps(event)}\n\n"`).
- Handle client disconnects gracefully by closing the PubSub subscription.
**Test scenarios:**
- Covers happy path: Connecting returns the initial state of active incidents.
- Covers edge cases: Client disconnect drops the Redis subscription without leaking tasks.

### U3. Next.js SSE Proxy and Frontend Consumer
**Goal:** Securely consume the SSE stream and update the React state.
**Files:**
- `frontend/src/app/api/stream/route.ts`
- `frontend/src/app/t/[tenantId]/incidents/page.tsx`
- `frontend/src/components/incident-feed-live.tsx`
**Approach:**
- Create `frontend/src/app/api/stream/route.ts` that retrieves the Supabase JWT and proxies the `StreamingResponse` from FastAPI.
- Refactor `IncidentsPage` to render a new Client Component `<IncidentFeedLive initialIncidents={incidents} />`.
- Use `useEffect` with standard browser `EventSource` pointing to `/api/stream`, which listens for updates and updates the local state array.
**Test scenarios:**
- Covers happy path: Receiving an SSE event updates the UI badge from "queued" to "report ready".

### U4. API Cost Protection & PromQL Standardization
**Goal:** Protect AWS and PMM infrastructure from rate-limiting via a caching layer, and finalize PromQL instant query logic.
**Files:**
- `src/sentineldb/collectors/cloudwatch.py`
- `src/sentineldb/collectors/prometheus.py`
**Approach:**
- Add a simple 60-second TTL cache class to wrap `client.get_metric_statistics` and `client.get`.
- Validate that `PrometheusCollector` uses an instant query (`/api/v1/query`), which it currently does. Add explicit documentation or typing to cement this assumption.
**Test scenarios:**
- Covers happy path: Sequential calls within 60s return cached EvidenceItem without hitting network.

---
## Scope Boundaries
- **Deferred to Follow-Up Work:** Bidirectional WebSockets. We explicitly scoped this feature to Server-Sent Events (SSE).