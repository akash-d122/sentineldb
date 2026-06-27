# Product Requirements Document
# SentinelDB - DBE Incident Analysis Assistant

**Version:** 1.2 - Reviewed and Implementation-Ready Draft  
**Author:** Akash Duddekunta  
**Status:** Reviewed Draft - Ready for Implementation Planning  
**Last Updated:** June 2026  
**Primary Goal:** Build a production-oriented, read-only DB incident analysis assistant that helps DBEs understand alerts faster using evidence from DB metrics, CloudWatch, PMM/Prometheus, and runbooks.

> **v1.2 Review Summary:** This revision tightens V1 scope, fixes CloudWatch and EC2/RDS feasibility issues, changes RCA output away from long narrative/confidence-heavy format, adds missing assumptions and dependencies, defines an evidence-first RCA contract, adds instance registry requirements, strengthens guardrails, adds testing/evaluation standards, and adds an Antigravity IDE + Claude Code development workflow.

---

## Table of Contents

1. Executive Summary
2. Product Goals and Strategy
3. V1 Scope, Non-Goals, and Assumptions
4. Users and Jobs To Be Done
5. Core User Workflows
6. Functional Requirements and Acceptance Criteria
7. RCA Output Contract
8. Evidence and Analysis Design
9. System Architecture
10. Data Sources and Collector Specifications
11. Security, Authentication, and Guardrails
12. Web Dashboard Requirements
13. Notification and Ticketing Requirements
14. Technical Stack and Data Models
15. Testing, Evaluation, and Observability
16. Development Workflow: Antigravity IDE + Claude Code
17. Risks and Mitigations
18. Roadmap
19. Success Metrics
20. Implementation Milestones
21. Open Questions

---

## 1. Executive Summary

### 1.1 Problem Statement

Database engineers handling MySQL and PostgreSQL incidents often spend 30 minutes to 2 hours gathering evidence before they can form a reliable RCA. The evidence is spread across database metadata, PMM/Prometheus dashboards, CloudWatch metrics, slow query data, alerts, and internal runbooks. This makes incident response slow, inconsistent, and dependent on individual DBE experience.

Small startups and growing engineering teams face the same pain with fewer DB experts. When the database slows down, engineers often guess, restart services, over-scale, or chase the wrong cause because they lack a structured incident analysis workflow.

### 1.2 Proposed Solution

SentinelDB is a threshold-triggered, read-only DB incident analysis assistant. When an alert fires, it:

1. Parses the alert.
2. Identifies the affected DB instance using an instance registry.
3. Collects read-only current metrics from MySQL/PostgreSQL.
4. Fetches relevant infrastructure and historical metrics from CloudWatch, PMM, and/or Prometheus.
5. Retrieves relevant runbook sections.
6. Applies deterministic RCA rules and evidence scoring.
7. Produces a short, scannable RCA report with proof bullets and safe next actions.
8. Sends the report to the dashboard, Slack/Teams, and a ticketing system.

The system is not an auto-remediation tool. It does not modify databases, infrastructure, or configuration. It only gathers evidence and recommends safe DBE checks.

### 1.3 Core Positioning

> Read-only, evidence-backed incident analysis for MySQL and PostgreSQL teams.

Avoid positioning V1 as "an autonomous AI DBA". That overpromises and creates trust problems. V1 should be presented as a DBE copilot that shortens evidence gathering and provides safe, structured recommendations.

### 1.4 V1 Success Criteria

| KPI | Baseline | V1 Target |
|---|---:|---:|
| Time from alert received to RCA ready | 30-120 min manual | < 5 minutes |
| Guardrail test pass rate | N/A | 100% |
| DB write capability | Possible manually | 0 writes from SentinelDB |
| Evidence hallucination rate | N/A | 0% in evidence section |
| DBE validation result | N/A | >= 80% Correct or Partially Correct |
| Ticket creation after report | Manual | < 60 sec after RCA ready |
| Dashboard incident list load time | N/A | < 2 sec |

---

## 2. Product Goals and Strategy

### 2.1 Primary V1 Goal

Build a portfolio-grade and company-demo-ready internal tool that proves Akash can design and implement production-style backend/AI reliability systems.

V1 should demonstrate:

- Database domain knowledge.
- Backend API design.
- Safe read-only integrations.
- Evidence-oriented AI system design.
- Incident workflow understanding.
- Testable guardrails.
- Clear dashboard and ticket output.

### 2.2 Secondary Business Goal

Use V1 as the foundation for a future productized service or SaaS for small teams that do not have dedicated DBEs.

Potential future offers:

- Weekly DB health reports.
- Read-only DB incident analysis setup.
- Safe SQL review assistant.
- PMM/Prometheus-based DB reliability dashboard.
- Managed DB observability and incident reporting for startups.

### 2.3 Strategy

Build in this order:

```text
Local simulated incident demo
-> EC2-hosted MySQL/PostgreSQL demo
-> Manager/internal showcase
-> anonymized case study
-> productized service validation
-> SaaS only after repeated buyer pain is proven
```

Do not jump directly to multi-tenant SaaS. V1 must first prove the incident analysis engine.

---

## 3. V1 Scope, Non-Goals, and Assumptions

### 3.1 V1 Scope

V1 supports:

- MySQL and PostgreSQL.
- EC2-hosted DB instances as the primary implementation target.
- RDS/Aurora as an adapter path if CloudWatch/RDS identifiers are configured, but not mandatory for the first working demo.
- Alert ingestion using Prometheus Alertmanager-compatible webhooks.
- Manual analysis trigger from dashboard.
- PMM/Prometheus historical metrics if available.
- CloudWatch metrics where available.
- Markdown runbooks stored in the repo.
- Read-only collector queries.
- Deterministic, evidence-first RCA reports.
- Slack or Teams notification.
- Jira ticket creation first, Freshdesk later.
- Single team/internal deployment.

### 3.2 V1 Hard Non-Goals

| Out of Scope | Reason |
|---|---|
| Auto-remediation | Too risky. V1 recommendations only. |
| Any database writes | Product-level non-negotiable. |
| LLM-generated executable SQL | Unsafe. Safe actions must come from pre-approved templates. |
| SSH or remote command execution | Avoid infrastructure risk and secrets exposure. |
| MongoDB and TiDB | Separate metric models. Later. |
| Multi-tenant SaaS | Requires auth, tenant isolation, billing, onboarding, security review. |
| Mobile app | Web dashboard only. |
| Full auth system | V1 can use static API key/private network. JWT later. |
| Config change recommendations as executable steps | Can mention "requires DBE approval", but cannot present as copy-paste action. |
| LLM fine-tuning | V1 uses structured evidence, deterministic rules, and constrained summarization. |
| On-prem support | Out of V1. Future only if strong demand appears. |

### 3.3 Key Assumptions

- V1 runs against test/sandbox databases first.
- Production or company data must not be used without explicit permission.
- DB credentials are read-only and scoped per environment.
- PMM/Prometheus may not always be available. RCA must degrade gracefully.
- CloudWatch EC2 default metrics do not include guest OS memory and filesystem usage unless CloudWatch Agent or another collector is already configured.
- RDS Enhanced Monitoring is optional and only available if enabled.
- `pg_stat_statements` may not be enabled on every PostgreSQL instance.
- MySQL slow query logs may not be available through SQL unless configured. PMM Query Analytics or Performance Schema should be the primary V1 path for query evidence.

### 3.4 Dependencies

- PostgreSQL for SentinelDB's own persistence.
- Python 3.12.
- FastAPI.
- A local Docker-based MySQL/PostgreSQL demo environment.
- Optional AWS credentials for CloudWatch/RDS testing.
- Optional PMM/Prometheus test endpoint.
- Markdown runbooks.
- LLM provider key for RCA wording, but the system must still generate a non-LLM fallback report.

---

## 4. Users and Jobs To Be Done

### 4.1 Persona 1 - In-House DBE

**Context:** Handles alerts for many MySQL/PostgreSQL instances.  
**Job:** Quickly understand what evidence changed, what likely caused the alert, and what safe checks to run next.  
**Success:** Can understand the incident direction in under 30 seconds and validate the proof in under 2 minutes.  
**Non-negotiable:** No write access. No unsafe recommendations.

### 4.2 Persona 2 - Engineering Manager

**Context:** Evaluates whether Akash can move toward backend/internal tooling/AI systems.  
**Job:** See a working, safe, production-aware system, not a chatbot wrapper.  
**Success:** Demo shows clear architecture, guardrails, tests, real/simulated metrics, and practical incident reports.

### 4.3 Persona 3 - Startup CTO / Small Team Lead

**Context:** Runs a small product without a dedicated DBE.  
**Job:** Get structured incident context when the DB slows down.  
**Success:** Receives a ticket/report that helps their engineers avoid blind debugging.

---

## 5. Core User Workflows

### 5.1 Automated Alert Workflow

```text
Alert fires
-> Alertmanager/PMM sends webhook
-> FastAPI validates payload
-> Incident row created
-> Analysis job queued
-> Worker collects evidence
-> RCA report generated
-> Dashboard updated
-> Slack/Teams notification sent
-> Jira ticket created
```

### 5.2 Manual Analysis Workflow

```text
DBE opens dashboard
-> Selects instance
-> Selects incident focus and time window
-> Clicks Run Analysis
-> Same collector/RCA pipeline runs
-> Report appears in dashboard
```

### 5.3 DBE Validation Workflow

```text
DBE opens RCA report
-> Reads ROOT CAUSE and WHY THIS IS MOST LIKELY
-> Checks source-tagged evidence bullets
-> Runs safe validation queries if needed
-> Marks report Correct / Partial / Wrong
-> Adds optional feedback note
```

This workflow is important because V1 learning comes from DBE validation labels.

---

## 6. Functional Requirements and Acceptance Criteria

### Epic 1 - Alert Ingestion

**Requirement:** SentinelDB must receive and parse Alertmanager-compatible webhook payloads.

**Acceptance Criteria:**

- `POST /api/v1/alerts/inbound` accepts Alertmanager webhook payloads.
- Payload validation rejects invalid payloads with 400.
- Valid payload creates an incident record within 2 seconds.
- Duplicate alerts for the same instance + alert type + active time window are deduplicated for 5 minutes.
- Alert source, severity, instance label, metric name, threshold, value, and timestamp are persisted.
- API returns quickly and does not wait for full RCA generation.

### Epic 2 - Instance Registry

**Requirement:** SentinelDB must map alert labels to connection details and metric source identifiers.

**Acceptance Criteria:**

- V1 supports a YAML instance registry.
- Registry maps `instance_id` to:
  - DB engine: MySQL or PostgreSQL.
  - Host and port.
  - Read-only credential reference.
  - Cloud provider type: EC2, RDS, or local demo.
  - AWS resource identifiers if available.
  - PMM/Prometheus service identifiers if available.
- Missing registry entry returns a clear `INSTANCE_NOT_REGISTERED` error and does not attempt analysis.

Example:

```yaml
instances:
  db-prod-01:
    engine: postgresql
    environment: demo
    host: localhost
    port: 5432
    credential_ref: pg_demo_ro
    cloud:
      provider: aws
      type: ec2
      instance_id: i-0123456789abcdef0
      region: ap-south-1
    monitoring:
      pmm_service_name: db-prod-01-postgres
      prometheus_job: postgres_exporter
```

### Epic 3 - Metric Collection

**Requirement:** SentinelDB must collect current and historical evidence without blocking the whole analysis when a source fails.

**Acceptance Criteria:**

- Collectors run with per-source timeout and return partial results when a source is unavailable.
- Every metric has: source, name, value, unit, timestamp, status, and raw reference.
- Unavailable metrics are represented explicitly as `UNAVAILABLE`, not omitted silently.
- Collection failures are visible in the report.
- Collector runtime target: < 120 seconds total for one incident.

### Epic 4 - Runbook Retrieval

**Requirement:** SentinelDB must retrieve relevant runbook snippets from local Markdown runbooks.

**Acceptance Criteria:**

- Runbooks stored under `runbooks/*.md`.
- V1 supports semantic search if embeddings are configured.
- V1 must also support keyword fallback search so runbook retrieval works without embedding setup.
- Report shows top match only by default, with optional additional matches in the dashboard.
- Low relevance results are not surfaced as authoritative guidance.

### Epic 5 - Guardrails

**Requirement:** SentinelDB must guarantee read-only behavior through design, not just prompting.

**Acceptance Criteria:**

- DB users are read-only.
- Application query catalog only contains approved read-only diagnostic queries.
- LLM cannot generate executable SQL.
- Any SQL shown to users must pass guardrail checks.
- DML/DDL/config changes are blocked and moved to `Requires Approval` if mentioned at all.
- Guardrail tests cover SQL comments, mixed case, multi-statement strings, semicolon chaining, CTEs, stored procedures, `SET`, grants, DDL, and common bypass attempts.

### Epic 6 - RCA Report Generation

**Requirement:** SentinelDB must produce short, evidence-first RCA reports that engineers can scan quickly.

**Acceptance Criteria:**

- Root cause summary is 1-3 lines maximum.
- Proof bullets are source-tagged and populated from collected evidence.
- Values in evidence bullets must match collected data exactly.
- Report includes "Why this is most likely" and "What to check next".
- Report avoids long essay-style explanation.
- Report includes exclusions where useful, such as "replication lag normal" or "disk latency normal".
- Report generation has a non-LLM fallback.
- RCA report fits the main diagnostic summary on one screen.

### Epic 7 - Dashboard

**Requirement:** SentinelDB must provide a web dashboard for live and historical incident analysis.

**Acceptance Criteria:**

- Incident feed shows active incidents and status.
- Report page renders the RCA output contract exactly.
- Evidence panel shows source, timestamp, and raw reference.
- DBE can mark report as Correct, Partial, Wrong, or False Alert.
- Dashboard has manual analysis trigger.
- Dashboard shows ticket/notification delivery status.

### Epic 8 - Ticketing and Notifications

**Requirement:** SentinelDB must notify the team and attach structured analysis to tickets.

**Acceptance Criteria:**

- Slack/Teams message sent after report generation.
- Jira ticket created after report generation.
- Ticket includes full structured RCA, not a long prose essay.
- Notification failure does not block ticket creation.
- Ticket failure is shown in dashboard with retry.
- Auto-ticket creation is treated as notification/data delivery, not automated decision-making.

---

## 7. RCA Output Contract

### 7.1 Design Principle

The RCA is not a model-written essay. It is an evidence-backed incident summary.

The system should produce:

- One short root cause summary.
- 3-7 proof bullets.
- Small scannable reason bullets explaining why this conclusion is most likely.
- Relevant logs, queries, metrics, or events.
- Safe next actions for the DBE.
- Explicit unknowns and missing evidence.

The engineer should understand the incident direction in under 30 seconds.

### 7.2 Required RCA Format

```text
[P1] CPU Usage Alert | db-prod-01 | 2026-06-01 10:05 UTC

ROOT CAUSE
Connection saturation is the most likely cause of high DB CPU. Active connections reached 423/500 while slow query volume spiked on the orders query path.

WHY THIS IS MOST LIKELY
- CPU and connection spike happened in the same 10-minute window.
- Slow query evidence points to repeated expensive reads, not replication or disk failure.
- Replication lag was normal, so replica delay is unlikely to be the primary cause.

EVIDENCE
- [CloudWatch] CPUUtilization 91.3% at 10:05 UTC, threshold 85%, 7-day same-time baseline 42%.
- [DB] Active connections 423/500, waiting connections 38.
- [PMM/QAN] Query fingerprint `SELECT * FROM orders WHERE status=?` increased to 12,847 calls in 30 min.
- [Slow query] Query_time 45.2s at 10:04:51 for orders status lookup.
- [Replication] Lag 0s. Not a contributing signal.

RUNBOOK
- Match: `runbooks/high_cpu_connection_saturation.md`
- Relevant step: Check connection pool size, active sessions, and explain plan for top query.

SAFE NEXT ACTIONS
1. Run approved active-session diagnostic query.
2. Run approved EXPLAIN diagnostic query for the flagged query fingerprint.
3. Check recent application deploy or traffic spike around 09:55-10:05 UTC.

REQUIRES DBE APPROVAL
- Killing sessions.
- Adding indexes.
- Restarting DB or application services.

EVIDENCE STATUS
- Collected: DB activity, CloudWatch CPU, PMM query data, replication status.
- Missing: application deploy events.
- RCA strength: High.
```

### 7.3 RCA Rules

- Maximum root cause length: 3 lines.
- Maximum proof bullets in ticket/Slack: 7.
- Dashboard may show more evidence in expandable panel.
- No paragraphs longer than 3 lines.
- No invented metric values.
- No confidence percentage as the main trust mechanism.
- If evidence is weak, say `RCA strength: Low` and list missing data.
- Cosine similarity is only a runbook retrieval relevance value. It must not dominate RCA confidence.
- Do not show a runbook match if the match is weak. Show `No strong runbook match found`.

### 7.4 RCA Strength Labels

Replace numeric confidence-heavy presentation with deterministic labels:

| Label | Meaning |
|---|---|
| High | Primary signal, at least one corroborating signal, and key alternatives ruled out. |
| Medium | Primary signal present, but one or more corroborating signals missing. |
| Low | Alert confirmed, but evidence is incomplete or multiple causes remain plausible. |

The label is computed by rules, not generated by the LLM.

---

## 8. Evidence and Analysis Design

### 8.1 Evidence-First Architecture

The RCA system has three layers:

1. **Collectors:** Fetch raw metrics, logs, and query fingerprints.
2. **Analyzer:** Applies deterministic rules and builds candidate causes.
3. **Summarizer:** Optionally uses an LLM to compress the selected cause into a clear 1-3 line summary.

The LLM must not be the source of evidence. It only helps with wording.

### 8.2 Candidate RCA Patterns for V1

V1 should include a small ruleset for common DB incidents:

| Pattern | Required Signals | Supporting Signals | Exclusions |
|---|---|---|---|
| Connection saturation | Active connections > threshold | Waiting sessions, connection spike | DB down false, replication lag not primary |
| Slow query CPU pressure | CPU high + query latency/calls spike | Top fingerprint, missing/weak index evidence | Disk latency normal |
| Replication lag | Lag > threshold | Write volume spike, replica CPU/IO pressure | Primary DB CPU not sole cause |
| DB endpoint unreachable | TCP/db connection failed | RDS/EC2 status check, recent events if available | Credential error handled separately |
| Storage pressure | Free storage below threshold | Disk latency/write latency, table growth | Query-only spike unlikely |

### 8.3 Evidence Items

Each evidence item must include:

```python
class EvidenceItem(BaseModel):
    source: Literal["db", "cloudwatch", "pmm", "prometheus", "runbook", "system"]
    label: str
    value: str | int | float | None
    unit: str | None
    timestamp: datetime | None
    status: Literal["OK", "WARN", "CRITICAL", "UNAVAILABLE"]
    raw_reference: str | None
    display_text: str
```

`display_text` is assembled by the system from values. It is not free-form LLM output.

### 8.4 Missing Evidence Handling

If a source fails:

```text
EVIDENCE STATUS
- Missing: PMM query analytics unavailable - request timed out after 10s.
- RCA strength reduced from High to Medium.
```

Never hide missing data.

---

## 9. System Architecture

### 9.1 Recommended V1 Architecture

Use a simple but durable backend architecture:

```text
FastAPI API
-> PostgreSQL persistence
-> Job table / worker process
-> Collector services
-> Analyzer and RCA renderer
-> Notification/ticket dispatchers
-> React dashboard
```

Avoid relying only on FastAPI `BackgroundTasks` for production-like incident processing. For V1, a lightweight persistent job table and worker process is enough. Celery/RQ/Arq can be added later if required.

### 9.2 Agent Graph

LangGraph can be used, but keep the first implementation simple. The graph should be deterministic and stateful:

```text
AlertReceived
-> ParseAlert
-> ResolveInstance
-> CreateAnalysisJob
-> CollectDBEvidence
-> CollectCloudEvidence
-> CollectHistoricalEvidence
-> RetrieveRunbooks
-> AnalyzeCandidateCauses
-> RenderRCAReport
-> PersistReport
-> DispatchNotifications
-> CreateTicket
```

### 9.3 Runtime Boundary

- LLM is optional for wording.
- Evidence collection works without LLM.
- Report rendering works without LLM.
- If LLM fails, use deterministic fallback summary.

### 9.4 Data Flow

```text
Alert payload
-> normalized AlertPayload
-> InstanceRegistry lookup
-> EvidenceBundle
-> CandidateCause list
-> SelectedCause
-> IncidentReport
-> Dashboard/Ticket/Slack views
```

---

## 10. Data Sources and Collector Specifications

### 10.1 Database Collectors

#### PostgreSQL V1 Collector

Approved read-only diagnostics:

- `pg_stat_activity`
- `pg_locks`
- `pg_stat_database`
- `pg_stat_replication`
- `pg_stat_statements` if installed
- database size and table size queries
- connection count and max connections

Preconditions:

- `pg_monitor` role or equivalent read permissions.
- `pg_stat_statements` optional but recommended.

#### MySQL V1 Collector

Approved read-only diagnostics:

- `SHOW PROCESSLIST`
- `SHOW GLOBAL STATUS`
- `SHOW VARIABLES LIKE 'max_connections'`
- `information_schema.innodb_trx`
- `performance_schema` statement summaries if enabled
- replication status read-only checks where available

Preconditions:

- `PROCESS`, `SELECT`, and `REPLICATION CLIENT` privileges as needed.
- Performance Schema or PMM Query Analytics recommended for top query evidence.

### 10.2 CloudWatch Collector

Important feasibility correction:

- EC2 default CloudWatch metrics include CPU, network, disk ops/bytes for supported volumes, and status checks.
- EC2 guest memory and filesystem usage are not available by default without CloudWatch Agent or another exporter.
- RDS CloudWatch includes DB-level service metrics such as CPU, connections, storage, latency, IOPS, replica lag, and freeable memory.
- RDS Enhanced Monitoring provides OS-level metrics only if enabled.

V1 behavior:

- Use available CloudWatch metrics only.
- Mark unavailable metrics explicitly.
- Do not claim memory/filesystem metrics are available unless the source is configured.

### 10.3 PMM/Prometheus Collector

V1 should use Prometheus-compatible query APIs for historical comparison:

- Current incident window: last 30-60 min.
- Same time previous day.
- Same time previous week.
- Optional 30-day baseline if data retention allows.

PMM Query Analytics should be preferred for query-level evidence when available.

### 10.4 Runbook Source

- Markdown files in `runbooks/`.
- Each runbook should include: symptoms, evidence to collect, likely causes, safe checks, escalation rules, unsafe actions.

Example runbook file:

```markdown
# High CPU - Connection Saturation

## Symptoms
- DB CPU above 85%.
- Active connections above 80% of max_connections.
- Waiting sessions increasing.

## Safe Checks
- Check active sessions.
- Check top query fingerprints.
- Check recent traffic/deploy changes.

## Requires Approval
- Killing sessions.
- Restarting services.
- Adding indexes.
```

---

## 11. Security, Authentication, and Guardrails

### 11.1 Security Principles

- Read-only by default.
- Least privilege credentials.
- No production secrets in code.
- No arbitrary SQL execution from LLM output.
- No shell/SSH execution.
- All incident actions auditable.

### 11.2 Database-Level Read-Only Enforcement

PostgreSQL example:

```sql
CREATE ROLE sentinel_ro WITH LOGIN PASSWORD '<strong_password>';
GRANT CONNECT ON DATABASE your_db TO sentinel_ro;
GRANT pg_monitor TO sentinel_ro;
GRANT USAGE ON SCHEMA public TO sentinel_ro;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO sentinel_ro;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO sentinel_ro;
```

MySQL example:

```sql
CREATE USER 'sentinel_ro'@'%' IDENTIFIED BY '<strong_password>';
GRANT SELECT, PROCESS, REPLICATION CLIENT ON *.* TO 'sentinel_ro'@'%';
FLUSH PRIVILEGES;
```

### 11.3 Application-Level Guardrails

Guardrails must be allowlist-based where possible.

Allowed:

- Predefined diagnostic queries from a query catalog.
- `SELECT`, `SHOW`, and `EXPLAIN` when explicitly approved.

Blocked:

- `INSERT`, `UPDATE`, `DELETE`, `TRUNCATE`, `MERGE`.
- `CREATE`, `DROP`, `ALTER`, `RENAME`.
- `GRANT`, `REVOKE`.
- `SET GLOBAL`, risky `SET SESSION`, config changes.
- `CALL` / stored procedures unless specifically allowlisted.
- Multiple statements in one string.
- Transaction control statements.
- Shell commands.

### 11.4 LLM Boundary

The LLM must not:

- Generate SQL that will be executed.
- Invent evidence.
- Choose values not present in `EvidenceBundle`.
- Recommend direct writes, restarts, failover, or config changes as safe actions.

The LLM may:

- Rewrite a selected deterministic cause into a concise sentence.
- Help phrase a ticket summary.
- Explain missing evidence in simple language.

---

## 12. Web Dashboard Requirements

### 12.1 Required V1 Screens

1. **Live Incident Feed**
   - Active incidents sorted by severity and time.
   - Status: Queued, Collecting, Analyzing, Report Ready, Ticket Created, Failed.

2. **Incident Report View**
   - RCA output contract rendered exactly.
   - Root cause, why most likely, evidence, runbook, safe actions, requires approval, missing evidence.

3. **Evidence Panel**
   - Raw metric values and timestamps.
   - Source status: collected/unavailable/error.
   - Expandable raw query/log snippets.

4. **Historical Incidents**
   - Filter by instance, alert type, status, DBE rating, date.

5. **Manual Analysis Trigger**
   - Instance selector.
   - Alert focus selector.
   - Time window.

### 12.2 V1 UI Boundaries

Avoid overbuilding:

- No full admin panel.
- No threshold configuration UI.
- No runbook editor.
- No multi-user access control.
- No billing/onboarding.

---

## 13. Notification and Ticketing Requirements

### 13.1 Slack/Teams Message

Short format:

```text
[P1] SentinelDB | CPU Usage Alert | db-prod-01
Root Cause: Connection saturation is the most likely cause of high DB CPU.
Proof: CPU 91.3%, connections 423/500, slow query spike detected.
RCA strength: High
Dashboard: <link>
```

### 13.2 Jira Ticket

Ticket title:

```text
[SentinelDB][P1] CPU Usage Alert on db-prod-01 - 2026-06-01T10:05:00Z
```

Ticket body sections:

1. Root Cause
2. Why This Is Most Likely
3. Evidence
4. Runbook
5. Safe Next Actions
6. Requires DBE Approval
7. Evidence Status
8. Dashboard Link

Ticket body must remain scannable.

---

## 14. Technical Stack and Data Models

### 14.1 Recommended Stack

| Layer | Technology | Notes |
|---|---|---|
| Language | Python 3.12 | Core backend. |
| API | FastAPI | Alert ingestion and dashboard API. |
| Persistence | PostgreSQL | Incidents, jobs, evidence, runbooks. |
| Frontend | React + Vite | Keep UI simple. |
| Collector HTTP | httpx | Async PMM/Prometheus calls. |
| AWS | boto3 | CloudWatch/RDS read-only APIs. |
| DB Drivers | psycopg / asyncpg, pymysql/aiomysql | Prefer modern maintained drivers. |
| Agent/Workflow | LangGraph optional | Useful after simple worker flow is stable. |
| SQL parsing | sqlparse + allowlist catalog | Do not rely on parser alone. |
| Validation | Pydantic v2 | Request/response models. |
| Tests | pytest, pytest-asyncio | Unit and integration tests. |
| Formatting | ruff format or black + ruff | Choose one standard. |

### 14.2 Core Models

```python
class AlertPayload(BaseModel):
    alert_id: UUID
    source: AlertSource
    status: Literal["firing", "resolved", "manual"]
    instance_id: str
    alert_type: AlertType
    severity: Severity
    metric_name: str | None
    metric_value: float | None
    threshold_value: float | None
    triggered_at: datetime
    raw_payload: dict[str, Any]

class InstanceConfig(BaseModel):
    instance_id: str
    engine: Literal["mysql", "postgresql"]
    host: str
    port: int
    credential_ref: str
    cloud: CloudResourceConfig | None
    monitoring: MonitoringConfig | None

class EvidenceItem(BaseModel):
    source: EvidenceSource
    label: str
    value: str | int | float | None
    unit: str | None
    timestamp: datetime | None
    status: EvidenceStatus
    raw_reference: str | None
    display_text: str

class CandidateCause(BaseModel):
    cause_type: str
    strength: Literal["High", "Medium", "Low"]
    why_most_likely: list[str]
    supporting_evidence_ids: list[UUID]
    excluded_causes: list[str]
    missing_evidence: list[str]

class IncidentReport(BaseModel):
    incident_id: UUID
    alert_payload: AlertPayload
    root_cause_summary: str
    why_most_likely: list[str]
    evidence: list[EvidenceItem]
    runbook_reference: RunbookMatch | None
    safe_next_actions: list[SafeAction]
    requires_approval: list[str]
    missing_evidence: list[str]
    rca_strength: Literal["High", "Medium", "Low"]
    generated_at: datetime
    status: IncidentStatus
```

---

## 15. Testing, Evaluation, and Observability

### 15.1 Required Tests

Unit tests:

- Alert payload parser.
- Instance registry resolver.
- Guardrail checker.
- Query catalog validation.
- RCA rules engine.
- Report renderer.
- Notification formatter.

Integration tests:

- Local PostgreSQL collector against Docker PostgreSQL.
- Local MySQL collector against Docker MySQL.
- CloudWatch collector using botocore Stubber.
- PMM/Prometheus collector using mocked HTTP responses.
- End-to-end alert -> incident -> report flow.

Snapshot/golden tests:

- High CPU + connection saturation incident.
- Slow query spike incident.
- Replication lag incident.
- Missing PMM data incident.
- DB unreachable incident.

Security tests:

- DML/DDL blocked.
- Multi-statement SQL blocked.
- Mixed-case bypass blocked.
- Comment-based bypass blocked.
- LLM cannot insert unsafe action into safe actions.

### 15.2 RCA Evaluation

Each generated report can be rated:

- Correct.
- Partially Correct.
- Wrong.
- Insufficient Evidence.
- False Alert.

Store DBE notes with the rating. This becomes the improvement loop.

### 15.3 Observability for SentinelDB Itself

Log and expose:

- Alert received count.
- Collector success/failure per source.
- RCA generation time.
- Ticket creation success/failure.
- Notification success/failure.
- Guardrail block count.
- LLM usage count and failure count.
- Missing evidence frequency.

---

## 16. Development Workflow: Antigravity IDE + Claude Code

### 16.1 Research-Backed Principles

Current agentic coding best practices from Claude Code and Antigravity workflows support this approach:

- Explore first, then plan, then code.
- Give the agent a verification method.
- Keep project instructions in `CLAUDE.md` and rules files.
- Use planning mode before edits.
- Keep context lean with focused files and tasks.
- Use subagents/parallel agents for research or review, not simultaneous edits to the same files.
- Review artifacts before allowing broad implementation.
- Use permissions to limit tools and file access.
- Use frequent commits and small tasks.
- Add adversarial review/security review for sensitive systems.

### 16.2 Recommended Repo Files Before Coding

Create these first:

```text
PRD.md
ARCHITECTURE.md
IMPLEMENTATION_PLAN.md
DECISIONS.md
TASKS.md
CLAUDE.md
.claude/rules/project-scope.md
.claude/rules/safety-guardrails.md
.claude/rules/testing.md
runbooks/high_cpu_connection_saturation.md
runbooks/replication_lag.md
runbooks/db_unreachable.md
```

### 16.3 CLAUDE.md Minimum Content

```markdown
# SentinelDB Project Rules

## Product Boundary
SentinelDB is a read-only DB incident analysis assistant. It must never write to monitored databases, execute shell commands on monitored servers, or generate executable remediation actions.

## Architecture
- FastAPI backend.
- PostgreSQL persistence.
- YAML instance registry for V1.
- Read-only DB collectors.
- Deterministic RCA rules before LLM summarization.
- LLM may only summarize selected evidence.

## Coding Rules
- Write tests before implementation for guardrails and RCA logic.
- Keep modules small.
- No secrets in repo.
- Use Pydantic models for external input/output.
- If requirements conflict, stop and ask.

## Verification Commands
- `pytest`
- `ruff check .`
- `ruff format --check .`
```

### 16.4 Antigravity Usage

Use Antigravity IDE as the project command center:

- Create one Antigravity project for the repo folder only.
- Keep permissions narrow.
- Do not connect real production secrets.
- Use artifact review for plans and implementation summaries.
- Use its IDE features for file navigation, diffs, and code review.
- Do not run multiple agents editing the same module at the same time.

### 16.5 Claude Code Usage Inside Antigravity

Use Claude Code for focused implementation tasks.

Recommended workflow per task:

```text
1. Ask Claude Code to inspect only relevant files.
2. Ask for a plan first.
3. Approve/edit the plan manually.
4. Let Claude implement one small task.
5. Run tests.
6. Ask Claude for review/security review.
7. Commit.
8. Start a fresh session or compact before next module.
```

Example prompt:

```text
Read PRD.md, ARCHITECTURE.md, and .claude/rules/safety-guardrails.md.
Do not edit files yet.
Plan the implementation for the guardrail checker only.
The guardrail must be allowlist-first, block DML/DDL/config changes, block multi-statement SQL, and include pytest tests.
Return the file list, test cases, and implementation steps.
```

Implementation prompt:

```text
Implement only Task 1 from IMPLEMENTATION_PLAN.md: guardrail checker and tests.
Do not touch collectors, API routes, dashboard, or LLM code.
Run pytest for the guardrail tests and fix failures.
Stop after tests pass and summarize changed files.
```

### 16.6 Context Management Rules

- Do not paste the whole PRD into every prompt. Reference `PRD.md`.
- Keep each session focused on one module.
- Use `/compact` when context grows large.
- Start a new session after completing a milestone.
- Maintain `DECISIONS.md` after every architectural decision.
- Maintain `TASKS.md` as the task source of truth.

### 16.7 Code Review Workflow

After each milestone:

1. Run tests.
2. Run lint/format checks.
3. Ask Claude Code for spec compliance review.
4. Ask for security review on guardrails, credentials, and DB collectors.
5. Manually inspect diff.
6. Commit.

Review prompt:

```text
Review the current diff against PRD.md.
Focus on:
- read-only safety
- evidence hallucination risk
- missing tests
- scope creep
- maintainability
Do not modify files. Return blocking issues first.
```

### 16.8 Pitfalls To Avoid

- Letting Claude build full-stack everything in one session.
- Allowing LLM-generated SQL execution.
- Mixing SaaS/V3 scope into V1.
- Building dashboard before core evidence/report pipeline works.
- Adding real production credentials early.
- Trusting CloudWatch EC2 memory/disk filesystem metrics without CloudWatch Agent.
- Treating cosine similarity as RCA confidence.
- Writing long AI explanations instead of proof bullets.

---

## 17. Risks and Mitigations

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| RCA wrong or misleading | Medium | Medium | Evidence-first report, DBE rating loop, deterministic rules, missing evidence shown. |
| LLM invents values | Medium | High | Evidence bullets rendered by system only. LLM cannot populate evidence values. |
| Unsafe SQL shown or executed | Low | Critical | Query catalog, guardrail parser, read-only DB user, tests. |
| CloudWatch metrics unavailable/incomplete | Medium | Medium | Mark unavailable, use DB/PMM fallback, do not block report. |
| PMM/Prometheus unavailable | Medium | Medium | Partial RCA with missing evidence status. |
| Scope creep into SaaS | High | Medium | V1 hard non-goals and milestone gates. |
| Claude Code creates messy architecture | Medium | Medium | Plan-first workflow, CLAUDE.md, small tasks, reviews, tests. |
| Company data/security risk | Medium | High | Use synthetic/sanitized data until explicit permission. No secrets in repo. |
| Dashboard overbuilt before engine works | Medium | Medium | Build CLI/API report pipeline first. Dashboard after stable report model. |

---

## 18. Roadmap

### V1A - Local Proof of Life

- Docker PostgreSQL or MySQL.
- Instance registry.
- Guardrail module.
- One collector.
- One simulated alert.
- Deterministic RCA report in CLI/API response.
- Tests for guardrails and report rendering.

### V1B - Backend MVP

- FastAPI alert endpoint.
- Persistent incidents/jobs/evidence tables.
- Worker process.
- PostgreSQL + MySQL collectors.
- PMM/Prometheus mock/stub collector.
- Runbook retrieval.
- RCA rules engine.

### V1C - Demo Product

- React dashboard.
- Manual trigger.
- Slack notification.
- Jira ticket creation.
- Golden incident scenarios.
- Demo README and architecture diagram.

### V2 - Internal Enhanced Version

- RDS/Aurora collector maturity.
- More alert types.
- Better historical baselines.
- Freshdesk integration.
- Multi-user auth.
- Threshold UI.

### V3 - SaaS/Productized Version

- Tenant isolation.
- Onboarding flow.
- Billing.
- Customer-facing settings.
- Audit logs and compliance.
- Pricing validation.

---

## 19. Success Metrics

### V1 Engineering Metrics

| Metric | Target |
|---|---:|
| Guardrail tests | 100% pass |
| RCA evidence hallucination | 0 |
| Local E2E alert-to-report | < 60 sec |
| Full alert-to-ticket target | < 5 min |
| Collector partial failure handling | 100% graceful |
| Golden incident tests | All pass |

### V1 Product Metrics

| Metric | Target |
|---|---:|
| DBE report rating | >= 80% Correct or Partial |
| DBE scan time for summary | < 30 sec |
| False alert/report flag | < 10% |
| Dashboard load time | < 2 sec |

---

## 20. Implementation Milestones

### Milestone 0 - Repo Setup

- Initialize repo.
- Add PRD, architecture docs, CLAUDE.md, rules.
- Add `pyproject.toml`, `ruff`, `pytest`.
- Add `.env.example` and `.gitignore`.

### Milestone 1 - Guardrails First

- Query catalog.
- SQL safety checker.
- Blocked action model.
- Unit tests for all blocked cases.

### Milestone 2 - Core Models and Persistence

- Pydantic models.
- PostgreSQL schema/migrations.
- Incident/job/evidence/report tables.

### Milestone 3 - Local DB Collector

- PostgreSQL collector first or MySQL collector first.
- Docker test DB.
- Collector tests.

### Milestone 4 - RCA Rules and Renderer

- EvidenceBundle.
- CandidateCause rules.
- RCA renderer.
- Golden incident tests.
- Non-LLM fallback report.

### Milestone 5 - Alert API and Worker

- Alert inbound endpoint.
- Instance registry.
- Analysis job worker.
- E2E simulated alert test.

### Milestone 6 - Monitoring Integrations

- CloudWatch collector with Stubber tests.
- PMM/Prometheus HTTP collector with mocked tests.

### Milestone 7 - Runbook Retrieval

- Markdown loader.
- Keyword fallback.
- Optional embeddings later.

### Milestone 8 - Dashboard and Integrations

- Incident list.
- Incident report page.
- Manual trigger.
- Slack/Jira integration.

---

## 21. Open Questions

These should be answered before or during early implementation:

1. Which DB engine should be first for V1A: PostgreSQL or MySQL?
2. Will the first demo be fully local Docker, EC2 sandbox, or company-sanctioned test instance?
3. Is PMM available for the demo environment, or should Prometheus/PMM be mocked initially?
4. Which ticketing system should be first: Jira or Freshdesk? Recommendation: Jira only for V1.
5. Which frontend style is preferred: minimal internal tool UI or polished portfolio demo UI?
6. Which LLM provider/model will be used at runtime, or should V1 start with deterministic-only reports?
7. Are runbooks synthetic/demo runbooks or sanitized company-like runbooks?

---

## Final V1 Rule

If a requirement does not help produce a safe, evidence-backed incident report for one DB alert, it should not enter V1.
