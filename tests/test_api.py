"""
Unit tests for the FastAPI API.
"""

from __future__ import annotations

import hashlib
import hmac
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from sentineldb.api.main import app
from sentineldb.core.config import settings

client = TestClient(app)


def test_health_check() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_post_alert_invalid_json(monkeypatch: pytest.MonkeyPatch) -> None:
    # Set the webhook secret to "testsecret" to match the hardcoded test header,
    # or just provide the correct HMAC so we bypass the 401 and hit the 422.
    monkeypatch.setattr(settings, "WEBHOOK_SECRET", "testsecret")
    mac = hmac.new(b"testsecret", b"not json", hashlib.sha256).hexdigest()
    response = client.post(
        "/api/v1/alerts/inbound",
        content="not json",
        headers={"X-Webhook-Signature": mac},
    )
    assert response.status_code == 422


def test_post_alert_wrong_hmac(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "WEBHOOK_SECRET", "supersecret")
    payload = {
        "instance_id": "db-1",
        "alert_type": "cpu_high",
        "severity": "P1",
    }
    response = client.post(
        "/api/v1/alerts/inbound",
        json=payload,
        headers={"X-Webhook-Signature": "wrong-signature"},
    )
    assert response.status_code == 401


@patch("sentineldb.api.routes_alerts.run_incident_analysis")
def test_post_alert_valid_payload_mocked_celery(
    mock_celery_task: MagicMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Disable HMAC for this test, or compute it correctly
    monkeypatch.setattr(settings, "WEBHOOK_SECRET", "testsecret")

    payload = {
        "instance_id": "db-1",
        "alert_type": "cpu_high",
        "severity": "P1",
        "metric_value": 95.0,
    }
    body_bytes = json.dumps(payload).encode("utf-8")
    mac = hmac.new(b"testsecret", body_bytes, hashlib.sha256).hexdigest()

    # Mock DB session
    mock_session = AsyncMock()
    mock_session.add = MagicMock()
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()

    # Mock the dependency injection to return our mock session
    from sentineldb.db.session import get_session

    app.dependency_overrides[get_session] = lambda: mock_session

    try:
        response = client.post(
            "/api/v1/alerts/inbound",
            content=body_bytes,
            headers={
                "X-Webhook-Signature": mac,
                "Content-Type": "application/json",
            },
        )
        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "accepted"
        assert "incident_id" in data

        # Check celery was dispatched
        mock_celery_task.delay.assert_called_once()
        args = mock_celery_task.delay.call_args[0]
        assert args[0] == data["incident_id"]  # incident_id str
        assert args[1]["instance_id"] == "db-1"  # payload dict
    finally:
        # Clean up
        app.dependency_overrides.pop(get_session, None)
