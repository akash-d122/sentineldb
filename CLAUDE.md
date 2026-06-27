@AGENTS.md

# Claude Code Project Instructions

**IMPORTANT: Read `AGENTS.md` for the full context and shared project rules.**

## Verification Commands
- `uv run pytest`
- `uv run ruff check .`
- `uv run ruff format --check .`

## Agent Workflow Rules
- Explore first, then plan, then code.
- Do not implement broad features in one prompt.
- Before editing, state the exact files to modify.
- After editing, summarize changed files and tests run.
- Ask for review after guardrail/security-sensitive changes.
- Keep implementation aligned with `docs/PRD.md`, `docs/ARCHITECTURE.md`, `docs/DECISIONS.md`, and `docs/plans/`.

## Detailed Rules
See `.claude/rules/` for:
- `safety-guardrails.md` — sqlparse enforcement details, blocked SQL patterns
- `testing.md` — test-first areas, golden test scenarios
- `project-scope.md` — V1A scope gate
- `agent-workflow.md` — standard workflow steps