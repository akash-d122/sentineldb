"""
Simulated E2E integration test for the full V1A stack.

Requires Docker Compose stack running: `docker compose up -d db`
Run with: `uv run pytest tests/test_e2e_simulated.py -m integration`
"""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine

from sentineldb.core.config import settings
from sentineldb.core.enums import AlertType, Severity
from sentineldb.core.models import AlertPayload
from sentineldb.db.models import IncidentReportORM
from sentineldb.worker.tasks import _analyze

integration = pytest.mark.skipif(
    os.environ.get("DOCKER_INTEGRATION") != "1",
    reason="Requires Docker Compose db service (DOCKER_INTEGRATION=1)",
)


@pytest.fixture
def mock_registry_host():
    """Mock registry loader to point 'db' to 'localhost' for tests running on host."""
    from sentineldb.registry.loader import InstanceRegistry

    original_resolve = InstanceRegistry.resolve

    def mocked_resolve(self, instance_id: str):
        instance = original_resolve(self, instance_id)
        if instance.host == "db":
            return instance.model_copy(update={"host": "127.0.0.1", "port": 5433})
        return instance

    with patch(
        "sentineldb.registry.loader.InstanceRegistry.resolve",
        side_effect=mocked_resolve,
        autospec=True,
    ):
        yield


@integration
@pytest.mark.asyncio
async def test_e2e_simulated_pipeline(mock_registry_host) -> None:
    """
    Test the core analysis pipeline end-to-end against a real PostgreSQL database.
    (Bypasses Celery/HTTP for speed, tests the core logic.)
    """
    import uuid

    # 1. Construct simulated payload
    incident_id = str(uuid.uuid4())
    payload = AlertPayload(
        instance_id="db-demo-01",  # Matches instances.yaml
        alert_type=AlertType.cpu_high,
        severity=Severity.P1,
        metric_value=95.0,
    )

    # 1.5. Pre-insert the Incident row (normally done by FastAPI route)
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.orm import sessionmaker

    from sentineldb.db.models import IncidentORM

    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    LocalSession = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)  # type: ignore

    try:
        async with LocalSession() as session:
            incident = IncidentORM(
                incident_id=uuid.UUID(incident_id),
                instance_id=payload.instance_id,
                alert_type=payload.alert_type.value,
                severity=payload.severity.value,
                metric_value=payload.metric_value,
                status="queued",
                raw_payload={},
                triggered_at=payload.triggered_at,
            )
            session.add(incident)
            await session.commit()
    finally:
        await engine.dispose()

    # 2. Run analysis (this calls the asyncpg collector, analyzer, renderer, and persists to DB)
    report = await _analyze(incident_id, payload)

    # 3. Verify report structure
    assert report.incident_id == incident_id
    assert report.rca_strength is not None
    assert report.root_cause_summary

    # Ensure evidence was collected from the real DB
    assert len(report.evidence) > 0
    active_conns = next((i for i in report.evidence if i.label == "active_connections"), None)
    assert active_conns is not None
    assert active_conns.value is not None  # We got a real number back

    # 4. Verify persistence
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.orm import sessionmaker

    LocalSession = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)  # type: ignore

    try:
        async with LocalSession() as session:
            stmt = select(IncidentReportORM).where(
                IncidentReportORM.incident_id == uuid.UUID(incident_id)
            )  # noqa: E501
            result = await session.execute(stmt)
            db_report = result.scalar_one_or_none()

            assert db_report is not None
            assert db_report.root_cause_summary == report.root_cause_summary
    finally:
        await engine.dispose()


@integration
@pytest.mark.asyncio
async def test_e2e_simulated_http() -> None:
    """
    Test the full stack via HTTP, covering FastAPI routing, HMAC validation,
    Celery task dispatch via Redis, and database persistence.
    Requires app and worker to be running (`docker compose up -d`).
    """
    import asyncio
    import hashlib
    import hmac
    import json

    import httpx

    payload = {
        "instance_id": "db-demo-01",
        "alert_type": "cpu_high",
        "severity": "P1",
        "metric_value": 90.0,
    }
    body_bytes = json.dumps(payload).encode("utf-8")

    # We use "test_webhook_secret" matching the local .env file
    mac = hmac.new(b"test_webhook_secret", body_bytes, hashlib.sha256).hexdigest()

    async with httpx.AsyncClient() as client:
        # Wait a moment for app to be healthy
        for _ in range(5):
            try:
                health = await client.get("http://127.0.0.1:8000/health")
                if health.status_code == 200:
                    break
            except httpx.RequestError:
                pass
            await asyncio.sleep(1)

        # Dispatch via FastAPI webhook
        response = await client.post(
            "http://127.0.0.1:8000/api/v1/alerts/inbound",
            content=body_bytes,
            headers={
                "X-Webhook-Signature": mac,
                "Content-Type": "application/json",
            },
        )
        assert response.status_code == 202, f"Failed: {response.text}"
        data = response.json()
        incident_id = data["incident_id"]

    # Poll DB directly for the completed report
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.orm import sessionmaker

    LocalSession = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)  # type: ignore

    try:
        async with LocalSession() as session:
            for _ in range(10):  # Wait up to 10 seconds for Celery to finish
                stmt = select(IncidentReportORM).where(
                    IncidentReportORM.incident_id == uuid.UUID(incident_id)
                )  # noqa: E501
                result = await session.execute(stmt)
                db_report = result.scalar_one_or_none()
                if db_report is not None:
                    break
                await asyncio.sleep(1)

            assert db_report is not None, "Report was never persisted by Celery worker"
            assert db_report.rca_strength in ["High", "Medium", "Low"]
    finally:
        await engine.dispose()
