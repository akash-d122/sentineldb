1. Name the file(s) and line(s) that will call this new file: No files will execute this file; it is a markdown planning document that will be read by developers or executing agents.
2. Confirm no existing file serves the same purpose: A directory listing of `docs/plans/` confirms no existing plan addresses removing V3 SaaS features, telemetry, and auth.
3. If this file reads/writes data files: Not applicable; this is a static markdown document.
4. Quote the user's current instruction verbatim: "are those after v1c demo things in the codebase really garbage and not worth having ? If yes remove and provide the reason"

# Project Realignment and Codebase Cleanup Plan

**Created:** 2026-07-03

## Summary
A comprehensive realignment pass to remove massive scope creep (SaaS features, Auth, Multi-tenancy, Real-time telemetry, A/B testing) that violates the PRD's V1 scope. The plan reverts the system to a clean, single-tenant incident analysis engine and restores the simple V1C React dashboard.

## Problem Frame
Recent development jumped straight from V1 (Local Proof of Life) to V3 (SaaS/Productized Version), adding features explicitly forbidden by the PRD's "V1 Hard Non-Goals":
- **Multi-tenant SaaS & Auth:** Added JWT, Supabase SSR auth, and Stripe mocks. This bloats the data model with `tenant_id` everywhere and requires complex security logic, distracting from the core RCA engine.
- **Next.js SaaS Dashboard:** The simple V1C dashboard was replaced with a deeply nested Next.js App Router structure (`t/[tenantId]/incidents/[incidentId]`).
- **Real-time Telemetry (SSE & Redis):** Added Redis pub/sub dependencies and streaming endpoints. V1 is designed to be a threshold-triggered analyzer (point-in-time snapshot), not a live metrics streaming platform.
- **PostHog A/B Testing:** Added experimentation flags for UI components before the core product is even validated.

These additions are "garbage" in the context of the V1 product—they dilute the core value proposition, increase infrastructure overhead (Redis, Supabase), and add thousands of lines of maintenance burden for zero immediate user value.

## Requirements
- **R1:** Strip all V3 Multi-tenancy, JWT Auth, and Stripe mock logic from the FastAPI backend.
- **R2:** Remove Redis pub/sub and Server-Sent Events (SSE) telemetry streaming from the backend.
- **R3:** Delete the bloated Next.js SaaS `frontend/` and restore the V1C Vite+React dashboard from `frontend_old/`.
- **R4:** Remove unneeded infrastructure dependencies (Redis, Supabase client, PostHog) from the project configuration.
- **R5:** Ensure the core V1 RCA engine and its tests still pass at 100%.

## Key Technical Decisions
- **Swap, don't refactor, the frontend:** The Next.js frontend is too intertwined with auth and multi-tenancy. We will completely delete `frontend/` and rename `frontend_old/` to `frontend/` to instantly restore the V1C state.
- **Backend rollback over git revert:** Since V3 features were merged into `master` alongside some legitimate fixes (e.g., linting), we will execute a forward-fix (deleting the V3 files/code) rather than a complex historical `git revert`.

---

## Implementation Units

### U1. Restore V1C Frontend Dashboard
**Goal:** Replace the bloated Next.js SaaS frontend with the original Vite+React V1C dashboard.
**Files:**
- `frontend/` (delete entire directory)
- `frontend_old/` (rename to `frontend/`)
**Approach:** 
1. Delete the `frontend/` directory (Next.js).
2. Rename `frontend_old/` to `frontend/`.
3. Verify `package.json` in the restored `frontend/` does not have PostHog or Supabase dependencies.
**Test expectation: none -- structural file operation.**

### U2. Strip Multi-tenancy and Auth from Backend
**Goal:** Remove JWT verification, tenant routing, and `tenant_id` data isolation from the API and models.
**Files:**
- `src/sentineldb/api/dependencies.py` (remove JWT/Auth checks)
- `src/sentineldb/api/routes_tenant.py` (delete)
- `src/sentineldb/api/main.py` (remove tenant router)
- `src/sentineldb/models/incident.py` or similar DB models (remove `tenant_id` if added)
- `alembic/versions/` (generate new migration to drop tenant_id)
- `generate_jwt.py`, `test_db.py`, `seed_incident.py` (delete these ad-hoc scripts)
**Approach:** 
1. Remove the JWT validation dependency (`get_current_tenant` / `verify_jwt`). 
2. Change API routes back to single-tenant (e.g., `/api/v1/incidents` instead of `/api/v1/t/{tenant_id}/incidents`).
3. Generate and apply an Alembic migration to cleanly drop the `tenant_id` column from the database schema.
**Test expectation: Happy path behaviors -- API tests pass without requiring a Bearer token.**

### U3. Remove Real-time Telemetry (SSE & Redis)
**Goal:** Remove Redis pub/sub dependencies and streaming endpoints that deviate from the point-in-time RCA model.
**Files:**
- `src/sentineldb/api/routes_stream.py` (delete)
- `src/sentineldb/api/main.py` (remove stream router)
- `src/sentineldb/services/incident.py` (remove Redis publish calls)
- `docker-compose.yml` (remove Redis service if added)
- `pyproject.toml` (remove Redis Python package if added)
**Approach:** Delete the streaming endpoints and the Redis pub/sub publishing logic from the incident service.
**Test expectation: none -- removing unused features.**

### U4. Clean up extraneous V3 Documentation
**Goal:** Remove the brainstorms, plans, and growth documents related to the V3 features.
**Files:**
- `docs/growth/ab-test-db-connection.md` (delete)
- `docs/brainstorms/2026-07-02-frontend-dashboard-v3-saas-requirements.md` (delete)
- `docs/brainstorms/2026-07-02-real-time-telemetry-collectors-requirements.md` (delete)
**Approach:** Delete the files to avoid confusing future agents about the project scope.
**Test expectation: none -- documentation cleanup.**

### Open Questions
- **Legitimate UI Fixes Lost:** Replacing the Next.js `frontend/` directory entirely will discard UI fixes made during V3 (e.g., shadcn/ui linting fixes). Since the V1C dashboard uses Vite+React (without Shadcn), these fixes are likely inapplicable. Are there any generic frontend fixes that must be ported back? *Assumption: No. Discarding the V3 frontend entirely is safe.*