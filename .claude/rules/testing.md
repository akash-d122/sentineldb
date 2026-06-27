# Testing Rules

## Test-First Areas
Write tests before implementation for:
- guardrail checker,
- query/action catalog,
- RCA renderer,
- analyzer rules,
- alert parser,
- instance registry.

## Required Commands
Run before claiming completion:

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

If tooling is not installed yet, say that clearly and add the setup task.

## Golden Tests
RCA output must have golden tests for:
- high CPU + connection saturation,
- slow query spike,
- replication lag,
- DB unreachable,
- missing PMM/CloudWatch evidence.
