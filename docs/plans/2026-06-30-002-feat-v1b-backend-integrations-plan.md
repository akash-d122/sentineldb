---
title: "feat: Implement V1B Backend Integrations (MySQL, CloudWatch, Notifications)"
type: feat
date: 2026-06-30
---

# Summary
This plan implements the V1B Backend MVP capabilities for SentinelDB. It expands the analysis engine to support MySQL (`aiomysql`), adds metric collection from AWS CloudWatch (`boto3`), and implements an asynchronous notification dispatcher for Slack and Jira.

# Problem Frame
The V1A foundation successfully proved the evidence-first RCA pipeline against local PostgreSQL databases. To meet the full V1 backend requirements, SentinelDB needs to collect evidence from multiple database engines (MySQL) and external metric providers (CloudWatch), then route the finalized incident reports to engineering teams via their existing communication channels (Slack/Jira).

# Requirements
- R1. Collect diagnostic evidence from MySQL instances using `aiomysql`.
- R2. Collect infrastructure metrics from AWS CloudWatch using `boto3` without blocking the async event loop.
- R3. Enforce SQL guardrails correctly depending on the target database engine (PostgreSQL vs MySQL).
- R4. Dispatch Slack and Jira notifications asynchronously after an incident report is generated.
- R5. Ensure notification failures do not mark the incident analysis itself as failed.

# Key Technical Decisions

- **Notification Task Decoupling:** Dispatch notifications via a separate Celery task (`dispatch_notifications`) triggered at the end of `run_incident_analysis`. This isolation ensures that a network timeout to Slack/Jira doesn't rollback or fail the successfully completed RCA analysis.
- **CloudWatch Async Execution:** The `boto3` library is inherently synchronous. To integrate cleanly with our async evidence collection pipeline (which runs via `asyncio.gather`), CloudWatch API calls will be wrapped using `asyncio.to_thread`.
- **Engine-Aware Guardrails:** The single `DIAGNOSTIC_CATALOG` will be split into `POSTGRES_CATALOG` and `MYSQL_CATALOG`. The `GuardrailChecker` will accept an `engine` parameter to validate queries against the appropriate allowlist.

# Implementation Units

### U1. Refactor Guardrails for Multi-Engine Support
- **Goal:** Update the guardrail checker and catalog to support both PostgreSQL and MySQL safe queries.
- **Requirements:** R3
- **Files:** 
  - `src/sentineldb/guardrails/catalog.py`
  - `src/sentineldb/guardrails/checker.py`
  - `tests/test_guardrails.py`
- **Approach:** Split the dictionary into `POSTGRES_CATALOG` and `MYSQL_CATALOG`. Update `GuardrailChecker.check(sql, engine="postgresql")` to route to the correct allowlist. 
- **Test scenarios:**
  - Valid Postgres query allowed with `engine="postgresql"`.
  - Valid Postgres query rejected with `engine="mysql"`.
  - Valid MySQL catalog queries allowed.

### U2. Implement MySQL Collector
- **Goal:** Build a read-only evidence collector for MySQL databases.
- **Requirements:** R1
- **Files:** 
  - `src/sentineldb/collectors/mysql.py`
  - `src/sentineldb/worker/tasks.py`
  - `tests/test_collector_mysql.py`
- **Approach:** Mirror the structure of `PostgresCollector`. Use `aiomysql.create_pool` to execute the MySQL diagnostic catalog queries concurrently. Wire it into the factory logic inside `tasks.py` `_analyze()` based on `instance.engine == "mysql"`.
- **Patterns to follow:** `PostgresCollector` in `src/sentineldb/collectors/postgres.py`.
- **Test scenarios:**
  - Happy path evidence collection for all MySQL queries.
  - Connection failure yields `UNAVAILABLE` items.
  - Per-query timeout logic successfully aborts hanging queries and returns `UNAVAILABLE`.

### U3. Implement CloudWatch Collector
- **Goal:** Fetch external infrastructure metrics (CPU, IOPS, etc.) from AWS CloudWatch.
- **Requirements:** R2
- **Files:** 
  - `src/sentineldb/collectors/cloudwatch.py`
  - `src/sentineldb/worker/tasks.py`
  - `tests/test_collector_cloudwatch.py`
- **Approach:** Create a `CloudWatchCollector`. Given an `InstanceConfig` containing `cloud="aws"`, use `boto3.client('cloudwatch')`. Wrap the synchronous `get_metric_statistics` calls in `asyncio.to_thread`. Merge the resulting items into the main `EvidenceBundle`.
- **Execution note:** Use `unittest.mock` or `moto` heavily in tests to simulate AWS responses.
- **Test scenarios:**
  - Happy path retrieval of standard RDS metrics (CPUUtilization, DatabaseConnections).
  - AWS credential/permission error yields `UNAVAILABLE` items without crashing the pipeline.

### U4. Notification Dispatcher & Models
- **Goal:** Create the abstract dispatcher and concrete Slack/Jira notification handlers.
- **Requirements:** R4, R5
- **Files:** 
  - `src/sentineldb/notifications/__init__.py`
  - `src/sentineldb/notifications/models.py`
  - `src/sentineldb/notifications/slack.py`
  - `src/sentineldb/notifications/jira.py`
  - `src/sentineldb/notifications/dispatcher.py`
  - `tests/test_notifications.py`
- **Approach:** Create a basic plugin system where `NotificationDispatcher.notify(report)` loops over configured handlers. `SlackHandler` uses `httpx` to POST a structured block kit message. `JiraHandler` uses `httpx` to create a Jira issue.
- **Test scenarios:**
  - Slack handler correctly formats the incident report into markdown blocks.
  - Network timeouts are caught and logged gracefully.

### U5. Celery Task Routing for Notifications
- **Goal:** Hook the notification dispatcher into the async workflow via Celery.
- **Requirements:** R4, R5
- **Files:** 
  - `src/sentineldb/worker/tasks.py`
  - `tests/test_e2e_simulated.py`
- **Approach:** Add a new Celery task `@celery_app.task` named `dispatch_notifications`. In `run_incident_analysis`, invoke `dispatch_notifications.delay(report.report_id)` before returning. The new task retrieves the report from the DB and passes it to the `NotificationDispatcher`.
- **Test scenarios:**
  - Celery task successfully pulls the report from the DB and triggers the dispatcher.
  - Mocked E2E test verifies that the notification task is enqueued.

# Scope Boundaries
- **Deferred for later:** PMM/Prometheus integration (focusing on CloudWatch first as a representative external integration), multi-tenant notification routing (routing by instance ID to specific channels).
- **Outside this product's identity:** Remediation auto-execution (Slack/Jira payloads are read-only and informative, not interactive buttons for auto-failover).
