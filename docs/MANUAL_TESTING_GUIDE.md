# SentinelDB — Manual Testing Guide

> **Scope:** V1C (Local Proof of Life + Demo Product)  
> **Last Updated:** 2026-07-03

---

## Prerequisites

1. **Python 3.12** with `uv` installed
2. **Docker + Docker Compose** for PostgreSQL, Redis, FastAPI, Celery worker
3. Install dependencies: `uv sync --all-extras`
4. Copy `.env.example` → `.env` and fill in passwords
5. Start infrastructure: `docker compose up -d`
6. Run migrations: `uv run alembic upgrade head`

### Quick Verification (no Docker needed)
```bash
uv run pytest tests/ -v --tb=short
uv run ruff check .
uv run ruff format --check .
```

---

## Feature 1: SQL Guardrail Safety

**Purpose:** Ensures only approved diagnostic queries can ever be executed against monitored databases. No DML, DDL, or arbitrary SQL passes through.

### Test 1.1: Approved Catalog Queries Pass
```bash
uv run pytest tests/test_guardrails.py::test_all_catalog_entries_allowed -v
```
**Expected:** All PostgreSQL and MySQL catalog entries are allowed.

### Test 1.2: DML/DDL Blocked
```bash
uv run pytest tests/test_guardrails.py -k "blocked" -v
```
**Expected:** INSERT, UPDATE, DELETE, TRUNCATE, CREATE, DROP, ALTER, GRANT, REVOKE, SET GLOBAL, multi-statement, comments, stored procedures — all blocked with descriptive `blocked_pattern`.

### Test 1.3: Cross-Engine Rejection
```bash
uv run pytest tests/test_guardrails.py::test_cross_engine_rejection -v
```
**Expected:** PostgreSQL SQL is rejected when engine is MySQL, and vice versa.

### Manual Edge Case Test
```python
from sentineldb.guardrails.checker import GuardrailChecker
checker = GuardrailChecker()

# Non-catalog SELECT → blocked
assert checker.check("SELECT * FROM users WHERE id = 1").allowed is False

# Catalog query with extra whitespace → blocked (exact match)
assert checker.check("  SELECT count(*)  FROM  pg_stat_activity  ").allowed is False

# Empty string → blocked
assert checker.check("").allowed is False
```

---

## Feature 2: Core Domain Models

**Purpose:** Validates Pydantic v2 data models enforce schema contracts.

```bash
uv run pytest tests/test_models.py -v
```

### Key Validations
| Test | What It Validates |
|------|-------------------|
| `test_alert_payload_valid_roundtrip` | Valid payload round-trips through JSON |
| `test_alert_payload_missing_instance_id_raises` | Required fields enforced |
| `test_evidence_item_ok_value_none_raises` | Value required when status ≠ UNAVAILABLE |
| `test_evidence_item_unavailable_classmethod` | Factory method works correctly |
| `test_evidence_bundle_all_unavailable` | Bundle detects all-unavailable state |
| `test_candidate_cause_empty_why_raises` | At least one "why" reason required |

---

## Feature 3: RCA Analyzer (Rules Engine)

**Purpose:** Deterministic root cause analysis from evidence — no LLM involved.

```bash
uv run pytest tests/test_analyzer.py -v
```

### Golden Test Scenarios
| Scenario | Input | Expected Cause | Strength |
|----------|-------|----------------|----------|
| DB unreachable | All items UNAVAILABLE | `db_unreachable` | High |
| Connection saturation | 423/500 active, 38 waiting | `connection_saturation` | High |
| Low connections | 300/500, no waiting | Does NOT fire saturation | — |
| CPU + slow queries | CPU 91%, slow 12847 | `slow_query_cpu_pressure` | High |
| CPU only (no slow data) | CPU 91% | `slow_query_cpu_pressure` | Medium |
| Replication lag | 120s lag, no write_volume | `replication_lag` | Medium |
| Nothing matches | Normal metrics | `unknown_cause` | Low |

---

## Feature 4: Evidence Collectors

### 4.1: PostgreSQL Collector
```bash
uv run pytest tests/test_collector_postgres.py -v
```
- Connection failure → all items UNAVAILABLE (no crash)
- Query timeout → partial UNAVAILABLE results
- All catalog queries pass guardrail check

### 4.2: MySQL Collector
```bash
uv run pytest tests/test_collector_mysql.py -v
```
- Same fault tolerance as PostgreSQL collector

### 4.3: CloudWatch Collector
```bash
uv run pytest tests/test_collector_cloudwatch.py -v
```
- Happy path with mocked boto3
- Missing datapoints → UNAVAILABLE
- API error → UNAVAILABLE

### 4.4: Prometheus Collector
```bash
uv run pytest tests/test_collector_prometheus.py -v
```
- Happy path with mocked httpx
- Missing results → UNAVAILABLE
- API error → UNAVAILABLE

---

## Feature 5: RCA Renderer

**Purpose:** Converts CandidateCause + EvidenceBundle into a structured IncidentReport.

```bash
uv run pytest tests/test_renderer.py -v
```

### Validations
- Report includes safe_next_actions for each cause type
- Report includes requires_approval for risky actions
- Evidence values come directly from collectors (not LLM-generated)
- Missing evidence is explicitly tracked

---

## Feature 6: Runbook Retriever

**Purpose:** Keyword-based markdown runbook matching.

```bash
uv run pytest tests/test_runbook_retriever.py -v
```

### Manual Test
Place markdown files in `runbooks/` directory. Trigger an alert and check the report's `runbook_reference` field for matched content.

---

## Feature 7: LLM Summarizer

**Purpose:** Optional polish of deterministic RCA summary via Gemini/LiteLLM.

```bash
uv run pytest tests/test_summarizer.py -v
```

### Key Behaviors
- No API key → returns None (deterministic report used)
- API error → returns None (graceful fallback)
- PII is scrubbed before sending to LLM (hostnames, IPs, usernames, SQL literals)

### Manual Test (requires GOOGLE_API_KEY)
Set `GOOGLE_API_KEY` in `.env`, trigger an incident, and verify:
- Report has `"llm_used": true`
- `root_cause_summary` is polished but factually matches evidence

---

## Feature 8: Notification Dispatch

**Purpose:** Async notifications to Slack, Jira, and Freshdesk after RCA completes.

```bash
uv run pytest tests/test_notifications.py -v
```

### Key Behaviors
- Missing webhook URL → gracefully skipped (no crash)
- All handlers are async
- Dispatcher catches individual handler failures
- Freshdesk uses httpx.AsyncClient (not sync)

### Manual Test (requires webhook URLs)
Set `SLACK_WEBHOOK_URL` and/or `JIRA_WEBHOOK_URL` in environment, trigger an incident, and verify messages arrive in the configured channels.

---

## Feature 9: API Endpoints

### 9.1: Health Check
```bash
curl http://localhost:8000/health
```
**Expected:** `{"status":"ok"}`

### 9.2: Alert Webhook
```bash
curl -X POST http://localhost:8000/api/v1/alerts/inbound \
  -H "Content-Type: application/json" \
  -d '{"instance_id":"db-demo-01","alert_type":"cpu_high","severity":"P1","metric_value":95.0}'
```
**Expected:** HTTP 202 `{"status":"accepted","incident_id":"<uuid>"}`

### 9.3: With HMAC Signature
```python
import hmac, hashlib, json
body = json.dumps({"instance_id":"db-demo-01","alert_type":"cpu_high","severity":"P1"}).encode()
sig = hmac.new(b"your_webhook_secret", body, hashlib.sha256).hexdigest()
# Include header: X-Webhook-Signature: <sig>
```

### 9.4: Incident Listing
```bash
curl http://localhost:8000/api/v1/incidents
curl "http://localhost:8000/api/v1/incidents?status=report_ready"
curl "http://localhost:8000/api/v1/incidents?instance_id=db-demo-01"
```
**Expected:** JSON array, supports filtering by status and instance_id.

### 9.5: Incident Detail
```bash
curl http://localhost:8000/api/v1/incidents/<incident_id>
```
**Expected:** Single incident object with all fields.

### 9.6: Incident Report
```bash
curl http://localhost:8000/api/v1/incidents/<incident_id>/report
```
**Expected:**
- Status `queued/collecting/analyzing` → HTTP 202 with progress message
- Status `report_ready` → Full RCA report JSON
- Status `failed` → HTTP 500

### 9.7: Manual Analysis Trigger
```bash
curl -X POST http://localhost:8000/api/v1/incidents/analyze \
  -H "Content-Type: application/json" \
  -d '{"instance_id":"db-demo-01","alert_type":"connection_saturation","severity":"P2"}'
```
**Expected:** HTTP 202 with incident_id. Invalid instance_id → HTTP 400.

### 9.8: Threshold Configuration
```bash
# List
curl http://localhost:8000/api/v1/config/thresholds

# Create
curl -X POST http://localhost:8000/api/v1/config/thresholds \
  -H "Content-Type: application/json" \
  -d '{"instance_id":"db-demo-01","metric_name":"cpu","warning_threshold":80,"critical_threshold":95}'

# Delete
curl -X DELETE http://localhost:8000/api/v1/config/thresholds/<config_id>
```

### API Test Suite
```bash
uv run pytest tests/test_api.py tests/test_api_config.py tests/test_api_incidents.py -v
```

---

## Feature 10: Instance Registry

```bash
uv run pytest tests/test_registry.py -v
```

### Manual Test
Edit `instances.yaml` to add a new instance:
```yaml
db-prod-01:
  engine: postgresql
  host: prod-db.internal
  port: 5432
  database: myapp
  username: sentinel_ro
  credential_ref: PROD_DB_PASSWORD
  cloud: aws
  monitoring: cloudwatch
```
Then trigger analysis against `db-prod-01`.

---

## Feature 11: E2E Integration (Docker required)

```bash
# Start full stack
docker compose up -d

# Run integration tests
DOCKER_INTEGRATION=1 uv run pytest tests/test_e2e_simulated.py -v
```

### What's Tested
1. **Direct pipeline test:** Creates incident, runs full analysis, verifies report in DB
2. **HTTP test:** Sends webhook, waits for Celery to process, polls DB for completed report

---

## Feature 12: Celery Worker Pipeline

### Manual Verification
1. Start worker: `docker compose up worker -d`
2. Send alert via API
3. Check Redis for task: `docker compose exec redis redis-cli KEYS "celery*"`
4. Check incident status progression: `queued` → `collecting` → `analyzing` → `report_ready`

### Failure Handling
- Worker retry: Tasks retry up to 3 times with 10s countdown
- Failed incidents: Status set to `failed`, not left dangling
- Connection cleanup: AsyncEngine disposed in `finally` blocks

---

## Failure Scenarios & Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| Database unreachable | All evidence items UNAVAILABLE, cause = `db_unreachable` |
| Single query timeout | Partial results, other items collected normally |
| Redis down | Celery task dispatch fails, incident stays `queued` |
| LLM API key missing | Deterministic report used (no crash) |
| LLM API error | Fallback to deterministic report |
| Invalid alert_type | FastAPI returns 422 validation error |
| Unregistered instance_id | Manual trigger returns 400 |
| WEBHOOK_SECRET in production | Missing = RuntimeError at first request |
| Notification webhook down | Logged warning, other handlers still fire |

---

## Quick Full Validation Checklist

```bash
# 1. All tests pass
uv run pytest tests/ -v --tb=short

# 2. Lint clean
uv run ruff check .

# 3. Format clean
uv run ruff format --check .

# 4. Docker stack healthy (if available)
docker compose up -d
docker compose ps

# 5. E2E integration (if Docker available)
DOCKER_INTEGRATION=1 uv run pytest tests/test_e2e_simulated.py -v
```
