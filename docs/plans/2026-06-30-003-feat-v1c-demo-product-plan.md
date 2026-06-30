---
title: "feat: Implement V1C Demo Product"
type: feat
date: 2026-06-30
---

# V1C Demo Product Implementation Plan

## Summary
Implement the V1C Demo Product capabilities for SentinelDB. This involves adding CORS middleware, building a new incident and manual trigger API router, developing a React + Vite + TypeScript dashboard under `frontend/`, and providing backend test coverage to ensure API robustness.

## Problem Frame
SentinelDB currently ingests alert webhooks and processes database diagnostics asynchronously through a backend pipeline. To make this incident assistant demo-ready and usable by database engineers (DBEs), we need REST APIs to query ingested incidents, inspect their generated root cause analysis (RCA) reports, and a React dashboard to view incidents and trigger manual investigations.

## Requirements
- **R1.** FastAPI app must support CORS for local dashboard access.
- **R2.** API must expose paginated listing of incidents (`GET /api/v1/incidents`).
- **R3.** API must expose specific incident details (`GET /api/v1/incidents/{incident_id}`).
- **R4.** API must expose incident RCA reports (`GET /api/v1/incidents/{incident_id}/report`), returning `202 Accepted` if not yet generated.
- **R5.** API must allow manual analysis triggers (`POST /api/v1/incidents/analyze`).
- **R6.** Minimal React + Vite + TypeScript dashboard must be implemented under `frontend/` to consume these APIs.
- **R7.** Backend must have unit and integration tests covering the new endpoints.

## Key Technical Decisions
- **Manual Analysis Task Alignment:** The manual trigger API constructs a standard `AlertPayload` object and feeds it into the existing `run_incident_analysis` Celery task. This guarantees that manual analysis runs execute the exact same collector, analyzer, and renderer pipeline.
- **Non-blocking Status Resolution:** If a client requests the RCA report via the API before the worker has persisted the report, the API returns HTTP `202 Accepted` with a message indicating that the report is in progress, rather than throwing a 404 error.
- **Tailwind CSS Styling:** Use Tailwind classes for the dashboard UI to quickly build a responsive and polished interface without external CSS files.
- **Vite React Bootstrapping:** Vite is selected over Create React App or Next.js for its simplicity and speed, fitting the lightweight nature of this internal tool demo.

## Implementation Units

### U1. FastAPI CORS Setup
- **Goal:** Enable cross-origin request handling in the FastAPI app.
- **Requirements:** R1
- **Dependencies:** None
- **Files:**
  - `src/sentineldb/api/main.py`
- **Approach:** Import and add `CORSMiddleware` in `main.py` with `allow_origins=["*"]` or configured dynamically for local development environments.
- **Test scenarios:**
  - Happy path: HTTP OPTIONS preflight request to `/health` returns correct CORS headers.

### U2. Incident and Report Routers
- **Goal:** Expose incidents, reports, and manual triggers via HTTP.
- **Requirements:** R2, R3, R4, R5
- **Dependencies:** U1
- **Files:**
  - `src/sentineldb/api/routes_incidents.py`
  - `src/sentineldb/api/main.py`
- **Approach:** Create a new APIRouter in `routes_incidents.py` and mount it in `main.py`. Provide GET endpoints for fetching single and multiple incidents. Implement the report fetching logic to check incident status (returning 202 if queued/analyzing). Implement the POST manual analyze endpoint to validate instance existence and enqueue Celery tasks.
- **Test scenarios:**
  - Happy path: Querying `/api/v1/incidents` returns serialized incident metadata.
  - Edge case: Querying report for a queued incident yields `202 Accepted`.
  - Edge case: Querying report for a non-existent incident yields `404 Not Found`.
  - Happy path: POST to `/analyze` with a valid instance triggers the celery task.
  - Error path: POST to `/analyze` with invalid instance returns `400 Bad Request`.

### U3. Backend Incident API Tests
- **Goal:** Provide test coverage for the new API endpoints.
- **Requirements:** R7
- **Dependencies:** U2
- **Files:**
  - `tests/test_api_incidents.py`
- **Approach:** Write pytest tests that mock the database session and the Celery `.delay()` calls to avoid executing real backend logic during API testing.
- **Test scenarios:**
  - Happy path: Retrieve list of incidents.
  - Happy path: Successful manual trigger queues incident.

### U4. React Dashboard Setup and Models
- **Goal:** Bootstrap Vite-based React project with Tailwind and TypeScript.
- **Requirements:** R6
- **Dependencies:** None
- **Files:**
  - `frontend/package.json`
  - `frontend/tsconfig.json`
  - `frontend/vite.config.ts`
  - `frontend/tailwind.config.js`
  - `frontend/src/types/api.ts`
- **Approach:** Initialize package.json targeting React 18 and Tailwind v3. Set up TS definitions representing `Incident` and `IncidentReport` structures to match the backend Pydantic models.
- **Test expectation:** none -- scaffolding and types setup.

### U5. Dashboard Incident Feed and Detail Pages
- **Goal:** Implement the user interface screens for viewing and triggering incidents.
- **Requirements:** R6
- **Dependencies:** U4
- **Files:**
  - `frontend/src/App.tsx`
  - `frontend/src/pages/IncidentFeedPage.tsx`
  - `frontend/src/pages/IncidentDetailPage.tsx`
- **Approach:** 
  - `IncidentFeedPage`: A table rendering active incidents with polling.
  - `IncidentDetailPage`: Displays the RCA report (Root Cause Summary, Why Most Likely, Evidence Table, Safe Actions).
  - Include a manual trigger button/modal on the feed page that posts to `/analyze`.
- **Test expectation:** none -- frontend visual components will be manually verified.

## Scope Boundaries
- **In-Scope:** Zero-auth setup for local network runs, React single-page app layout with simple context-based routing.
- **Deferred to Follow-Up Work:** Dynamic query-building interfaces, user login and authentication, real-time Slack interactive actions.

## Verification
- Run backend tests `uv run pytest tests/test_api_incidents.py`.
- Run frontend `npm run dev` and perform an end-to-end manual trigger, confirming the RCA report successfully renders in the UI.
