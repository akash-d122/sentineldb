# Agent Workflow Rules

## Standard Flow
1. Read relevant docs/files.
2. Plan before editing.
3. Edit one module at a time.
4. Run focused tests.
5. Run lint/format checks when relevant.
6. Summarize changed files and verification output.

## Context Management
- Do not paste the whole PRD into prompts repeatedly.
- Reference `PRD.md`, `ARCHITECTURE.md`, and `TASKS.md`.
- Start a fresh session per milestone.
- Compact context when needed.

## Review
After security-sensitive changes, run a review focused on:
- read-only safety,
- unsafe SQL/action leaks,
- evidence hallucination,
- missing tests,
- scope creep.
