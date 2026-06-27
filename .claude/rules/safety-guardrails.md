# Safety Guardrail Rules

## Absolute Blocks
Never execute or generate executable actions for:
- INSERT, UPDATE, DELETE, TRUNCATE, MERGE
- CREATE, ALTER, DROP, RENAME
- GRANT, REVOKE
- SET GLOBAL or risky config changes
- KILL SESSION / terminate backend as safe action
- service restart
- failover
- SSH commands
- shell commands on monitored hosts

## Allowed Safe Actions
Only approved read-only diagnostic checks:
- SELECT from safe metadata/stat views
- SHOW diagnostic statements
- EXPLAIN for a flagged query fingerprint
- viewing metrics/log references already collected by safe collectors

## LLM Boundary
The LLM may not generate SQL for execution. It may only summarize a selected deterministic cause.

## Evidence Rule
Evidence values must come from collectors. Never invent or infer exact numbers.
