# SentinelDB Agent Rules

This file (`AGENTS.md`) is the **single authoritative rules file** for all agent tools (Antigravity IDE, Claude Code, etc.) working on the SentinelDB project.

## Product Boundary
SentinelDB is a read-only DB incident analysis assistant for MySQL/PostgreSQL incidents.
It gathers evidence, applies deterministic RCA rules, renders concise evidence-backed reports, and sends notifications/tickets.

## Non-Negotiable Safety Rules
- Never write to monitored databases.
- Never execute DML/DDL/config changes against monitored databases.
- Never run SSH or shell commands on monitored infrastructure.
- Never let an LLM generate SQL that will be executed.
- Safe actions must come from an approved diagnostic query/action catalog.
- Unsafe actions go under `REQUIRES DBE APPROVAL`, never under `SAFE NEXT ACTIONS`.
- Evidence values must come from collectors, not from LLM-generated text.

## V1 Scope
Build V1A first:
1. Documentation and architecture setup.
2. Guardrail checker with tests.
3. Core Pydantic models.
4. One local DB collector.
5. Evidence-first RCA renderer.
6. Simulated alert-to-report flow.

Do not build dashboard, Jira, Slack, CloudWatch, PMM, LangGraph, or SaaS features until V1A passes tests.

## Architecture Principles
- Evidence-first, LLM-second.
- Collectors produce raw evidence.
- Deterministic analyzer selects candidate cause.
- Renderer creates proof bullets from collected evidence.
- LLM may only compress selected evidence into a short root cause sentence.
- Non-LLM fallback report is mandatory.
- Missing evidence must be shown explicitly.

## Preferred Stack
- Python 3.12
- `uv` for dependency/environment management
- FastAPI for API layer
- Celery + Redis for async processing
- PostgreSQL + SQLAlchemy 2.0 (async) + Alembic for persistence
- `asyncpg` (PG) and `aiomysql` (MySQL) for read-only collectors
- `sqlparse` + allowlist catalog for guardrails
- LiteLLM + Gemini 2.5 Flash-Lite for LLM summarization
- Pydantic v2 for models
- `pytest` for tests
- `ruff` for lint/format
- Docker + Docker Compose for local infrastructure

## Coding Standards
- Type hints for all public functions.
- Small modules with single responsibility.
- Pure functions for guardrails/analyzer/renderer where possible.
- No secrets in code or committed files.
- `.env` must stay gitignored.
- Use clear names like `EvidenceItem`, `GuardrailResult`, `CandidateCause`, `IncidentReport`.

## Common Agent Pitfalls
- **Building multiple pipeline layers in one session:** Do not try to build collectors, analyzers, and the API simultaneously. Work on one small module at a time.
- **Allowing arbitrary SQL execution outside diagnostic catalog:** Always enforce `sqlparse` and allowlists.
- **Letting LLM produce evidence values:** The LLM receives structured summaries and only refines phrasing. Values come directly from metrics/logs.
- **Adding integrations too early:** Do not add CloudWatch, PMM, Slack, or Jira before the local DB collector pipeline passes tests.
- **Running long sessions without compaction:** Restart or `/compact` sessions to prevent context dilution when completing a module.

## Cross-References
- `CLAUDE.md`: Claude-Code-specific instructions (e.g. verification commands).
- `docs/PRD.md`: Full functional requirements and acceptance criteria.
- `docs/ARCHITECTURE.md`: Module layout and system design.
- `docs/DECISIONS.md`: Architectural decision records (ADRs).
