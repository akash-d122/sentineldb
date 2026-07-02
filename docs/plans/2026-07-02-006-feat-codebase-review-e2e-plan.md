# E2E Testing & Codebase Review Plan

**Target repo:** `.`

## Summary
Orchestrate a complete codebase architecture and security audit using specialized review skills (`/code-review`), followed by end-to-end execution of the integration suite against a live Docker-backed database (no mocked unit tests). This ensures both static code quality and runtime reliability under real data loads.

## Problem Frame
The current verification relies heavily on isolated unit tests which mock out real database interactions. A full verification requires exercising the integration tests against a real PostgreSQL instance and running an automated architecture/security review to catch structural anti-patterns.

## Requirements
- Run a codebase-wide automated review utilizing `/code-review`.
- Ensure architecture aligns with `AGENTS.md` principles (Evidence-first, no LLM-generated SQL execution, strict DML/DDL blocks).
- Execute the E2E simulation (`tests/test_e2e_simulated.py`) against a live Docker Compose stack.
- Prevent regression of recently added features (Next.js tenant auth, FastAPI async handlers).

## Key Technical Decisions
- **Live Integration Environment:** `docker compose up -d db redis` will be used to spawn the real infrastructure required by `DOCKER_INTEGRATION=1`.
- **Review Scope:** Review tools will target the FastAPI backend (`src/sentineldb/`) and Next.js frontend (`frontend/src/`) using the `code-review` skill.

---

### U1. Static Code and Security Review
**Goal:** Execute automated code reviews across the entire repository to find bugs, reuse/simplification opportunities, and security risks.
**Files:**
- `src/` (Entire backend)
- `frontend/src/` (Entire frontend)
**Approach:** 
- Invoke the `code-review` skill on the backend directory to flag anti-patterns, synchronous I/O blocks in FastAPI, and SQL injection vectors.
- Invoke the `code-review` skill on the Next.js frontend to ensure SSR cache safety (`cache: "no-store"`) and correct `getUser()` token handling.
- Review findings against the "Non-Negotiable Safety Rules" in `AGENTS.md`.

### U2. Architecture Audit
**Goal:** Manually review the structural integrity of the application against its core tenets.
**Files:**
- `docs/ARCHITECTURE.md`
- `src/sentineldb/core/`
- `src/sentineldb/worker/`
**Approach:**
- Verify the Celery worker and FastAPI API layers adhere to the "Evidence-first, LLM-second" boundary.
- Ensure the database guardrail system correctly rejects DML/DDL execution in the catalog logic.
- Document any architectural deviations as follow-up tasks.

### U3. Infrastructure Provisioning (Real Data Setup)
**Goal:** Spin up the Docker stack required for true end-to-end testing without mock data.
**Files:**
- `docker-compose.yml`
**Approach:**
- Start the auxiliary services (`db`, `redis`) using `docker compose up -d db redis`.
- Wait for health checks to pass (`pg_isready` and `redis-cli ping`).
- Ensure `instances.yaml` is configured to point to `localhost:5433` (the mapped port for the testing DB).

### U4. Integration and E2E Test Execution
**Goal:** Run the end-to-end simulated test pipeline against the live database.
**Files:**
- `tests/test_e2e_simulated.py`
**Approach:**
- Execute the test suite with integration flags enabled: `DOCKER_INTEGRATION=1 uv run pytest tests/test_e2e_simulated.py -v`.
- Observe real queries hitting the database, Celery task dispatches (if testing the full HTTP path), and real RCA report generation without mock data.
- Collect and summarize the test results.

---
## Scope Boundaries
- **Deferred to Follow-Up Work:** Fixing low-severity issues surfaced during the static review (only critical architecture/security bugs will be addressed immediately during the E2E verification loop).