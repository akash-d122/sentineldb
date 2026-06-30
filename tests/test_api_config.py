"""
Tests for Threshold Configuration API.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from sentineldb.api.dependencies import verify_jwt
from sentineldb.api.main import app
from sentineldb.db.models import ThresholdConfigORM
from sentineldb.db.session import get_session

# Override the auth dependency for all API tests
app.dependency_overrides[verify_jwt] = lambda: "test-user-id"

client = TestClient(app)

@pytest.fixture
def mock_session():
    session = AsyncMock()
    session.add = MagicMock()
    app.dependency_overrides[get_session] = lambda: session
    yield session
    app.dependency_overrides.pop(get_session, None)


@pytest.mark.asyncio
async def test_list_thresholds(mock_session: AsyncMock) -> None:
    config = ThresholdConfigORM(
        id=uuid.uuid4(),
        instance_id="test-db",
        metric_name="cloudwatch_cpu",
        warning_threshold=70.0,
        critical_threshold=90.0,
        updated_at=datetime.now(UTC),
    )
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [config]
    mock_session.execute.return_value = mock_result

    response = client.get("/api/v1/config/thresholds")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["instance_id"] == "test-db"
    assert data[0]["metric_name"] == "cloudwatch_cpu"


@pytest.mark.asyncio
async def test_create_threshold_new(mock_session: AsyncMock) -> None:
    # First execute returns no existing record
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None
    mock_session.execute.return_value = mock_result

    payload = {
        "instance_id": "test-db",
        "metric_name": "db_connections",
        "warning_threshold": 80.0,
        "critical_threshold": 100.0,
    }

    response = client.post("/api/v1/config/thresholds", json=payload)
    assert response.status_code == 201

    data = response.json()
    assert data["instance_id"] == "test-db"
    assert "id" in data

    mock_session.add.assert_called_once()
    mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_threshold_existing(mock_session: AsyncMock) -> None:
    existing = ThresholdConfigORM(
        id=uuid.uuid4(),
        instance_id="test-db",
        metric_name="db_connections",
        warning_threshold=50.0,
        critical_threshold=60.0,
        updated_at=datetime.now(UTC),
    )
    # First execute returns existing record
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = existing
    mock_session.execute.return_value = mock_result

    payload = {
        "instance_id": "test-db",
        "metric_name": "db_connections",
        "warning_threshold": 80.0,
        "critical_threshold": 100.0,
    }

    response = client.post("/api/v1/config/thresholds", json=payload)
    assert response.status_code == 201

    assert existing.warning_threshold == 80.0
    mock_session.add.assert_not_called()
    mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_threshold(mock_session: AsyncMock) -> None:
    config_id = uuid.uuid4()
    existing = ThresholdConfigORM(
        id=config_id,
        instance_id="test-db",
        metric_name="db_connections",
        warning_threshold=50.0,
        critical_threshold=60.0,
        updated_at=datetime.now(UTC),
    )
    mock_session.get.return_value = existing

    response = client.delete(f"/api/v1/config/thresholds/{config_id}")
    assert response.status_code == 204

    mock_session.delete.assert_awaited_once_with(existing)
    mock_session.commit.assert_awaited_once()
