from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from sentineldb.api.dependencies import verify_jwt
from sentineldb.api.main import app
from sentineldb.core.enums import IncidentStatus
from sentineldb.db.models import IncidentORM, IncidentReportORM
from sentineldb.db.session import get_session

# Override the auth dependency for all API tests
app.dependency_overrides[verify_jwt] = lambda: {"sub": "test-user-id", "tenant_id": "00000000-0000-0000-0000-000000000000"}

client = TestClient(app)


@pytest.fixture
def mock_session():
    session = AsyncMock()
    session.add = MagicMock()
    app.dependency_overrides[get_session] = lambda: session
    yield session
    app.dependency_overrides.pop(get_session, None)


@pytest.mark.asyncio
async def test_get_incidents_empty(mock_session: AsyncMock) -> None:
    # Setup mock
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_session.execute.return_value = mock_result

    response = client.get("/api/v1/incidents")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_get_incidents_list(mock_session: AsyncMock) -> None:
    incident_1 = IncidentORM(
        incident_id=uuid.uuid4(),
        instance_id="test-db",
        alert_type="cpu_high",
        severity="P1",
        metric_value=90.0,
        threshold_value=80.0,
        triggered_at=datetime.now(UTC),
        status=IncidentStatus.queued.value,
        raw_payload={"source": "test"},
        created_at=datetime.now(UTC),
    )
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [incident_1]
    mock_session.execute.return_value = mock_result

    response = client.get("/api/v1/incidents")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["instance_id"] == "test-db"
    assert data[0]["alert_type"] == "cpu_high"


@pytest.mark.asyncio
async def test_get_incident_by_id(mock_session: AsyncMock) -> None:
    incident_id = uuid.uuid4()
    incident = IncidentORM(
        incident_id=incident_id,
        instance_id="test-db-2",
        alert_type="slow_query",
        severity="P2",
        triggered_at=datetime.now(UTC),
        status=IncidentStatus.queued.value,
        created_at=datetime.now(UTC),
    )
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = incident
    mock_session.execute.return_value = mock_result

    response = client.get(f"/api/v1/incidents/{incident_id}")
    assert response.status_code == 200
    assert response.json()["instance_id"] == "test-db-2"


@pytest.mark.asyncio
async def test_get_report_states_queued(mock_session: AsyncMock) -> None:
    incident_id = uuid.uuid4()
    incident_queued = IncidentORM(
        incident_id=incident_id,
        instance_id="db-1",
        alert_type="db_unreachable",
        severity="P1",
        triggered_at=datetime.now(UTC),
        status=IncidentStatus.queued.value,
    )
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = incident_queued
    mock_session.execute.return_value = mock_result

    resp_queued = client.get(f"/api/v1/incidents/{incident_id}/report")
    assert resp_queued.status_code == 202
    assert "in progress" in resp_queued.json()["message"]


@pytest.mark.asyncio
async def test_get_report_states_ready(mock_session: AsyncMock) -> None:
    incident_id = uuid.uuid4()
    incident_ready = IncidentORM(
        incident_id=incident_id,
        instance_id="db-2",
        alert_type="db_unreachable",
        severity="P1",
        triggered_at=datetime.now(UTC),
        status=IncidentStatus.report_ready.value,
    )
    report = IncidentReportORM(
        report_id=uuid.uuid4(),
        incident_id=incident_id,
        rca_strength="High",
        root_cause_summary="DB is down",
        why_most_likely=[],
        evidence=[],
        safe_next_actions=[],
        requires_approval=[],
        missing_evidence=[],
        llm_used=False,
        generated_at=datetime.now(UTC),
    )

    # We call execute twice: first for incident, second for report
    mock_result_incident = MagicMock()
    mock_result_incident.scalars.return_value.first.return_value = incident_ready

    mock_result_report = MagicMock()
    mock_result_report.scalars.return_value.first.return_value = report

    mock_session.execute.side_effect = [mock_result_incident, mock_result_report]

    resp_ready = client.get(f"/api/v1/incidents/{incident_id}/report")
    assert resp_ready.status_code == 200
    assert resp_ready.json()["root_cause_summary"] == "DB is down"


@pytest.mark.asyncio
async def test_manual_trigger_invalid_instance() -> None:
    payload = {"instance_id": "unknown-db", "alert_type": "cpu_high"}
    response = client.post("/api/v1/incidents/analyze", json=payload)
    assert response.status_code == 400
    assert "INSTANCE_NOT_REGISTERED" in response.json()["detail"]


@patch("sentineldb.services.incident.run_incident_analysis")
@pytest.mark.asyncio
async def test_manual_trigger_success(
    mock_celery_task: MagicMock, mock_session: AsyncMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    from sentineldb.registry.loader import InstanceNotRegistered
    from sentineldb.registry.models import InstanceConfig

    def mock_resolve(instance_id: str) -> InstanceConfig:
        if instance_id == "test-db":
            return InstanceConfig(
                instance_id="test-db",
                engine="mysql",
                host="localhost",
                port=3306,
                database="test",
                username="test",
                credential_ref="MYSQL_PASSWORD",
            )
        raise InstanceNotRegistered(instance_id)

    import sentineldb.api.routes_incidents

    monkeypatch.setattr(sentineldb.api.routes_incidents._registry, "resolve", mock_resolve)

    payload = {"instance_id": "test-db", "alert_type": "cpu_high"}

    response = client.post("/api/v1/incidents/analyze", json=payload)
    assert response.status_code == 202
    assert response.json()["status"] == "accepted"
    assert "incident_id" in response.json()

    mock_session.add.assert_called_once()
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once()
    mock_celery_task.delay.assert_called_once()
