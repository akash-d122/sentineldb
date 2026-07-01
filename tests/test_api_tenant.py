import uuid
from unittest.mock import AsyncMock

import pytest

from sentineldb.api.main import app

# Since we use testclient with dependency overrides, tenant_context might be tricky.
# We'll use pytest-asyncio and verify HTTP routing directly.


@pytest.fixture
def mock_session() -> AsyncMock:
    session = AsyncMock()
    return session


@pytest.fixture
def client(mock_session: AsyncMock):
    from fastapi.testclient import TestClient

    from sentineldb.api.dependencies import verify_jwt
    from sentineldb.db.session import get_session

    app.dependency_overrides[get_session] = lambda: mock_session
    app.dependency_overrides[verify_jwt] = lambda: {
        "sub": "test-user-id",
        "tenant_id": "00000000-0000-0000-0000-000000000000",
    }

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_onboard_tenant(client, mock_session: AsyncMock) -> None:
    from unittest.mock import MagicMock
    # Setup mock to return None, meaning tenant not found
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None
    mock_session.execute.return_value = mock_result

    response = client.post(
        "/api/v1/tenant/onboarding", json={"name": "Test Tenant", "plan_tier": "pro"}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Tenant"
    assert data["plan_tier"] == "pro"
    assert data["billing_status"] == "active"
    assert data["tenant_id"] == "00000000-0000-0000-0000-000000000000"

    # Assert session.add was called for TenantORM and ThresholdConfigORM
    assert mock_session.add.call_count == 2
    assert mock_session.commit.call_count == 1


@pytest.mark.asyncio
async def test_get_billing_status(client, mock_session: AsyncMock) -> None:
    from unittest.mock import MagicMock
    # Setup mock to return a tenant
    mock_result = MagicMock()

    class DummyTenant:
        tenant_id = uuid.UUID("00000000-0000-0000-0000-000000000000")
        name = "Test Tenant"
        billing_status = "active"
        stripe_customer_id = "cus_mock_123"
        plan_tier = "free"

    mock_result.scalars.return_value.first.return_value = DummyTenant()
    mock_session.execute.return_value = mock_result

    response = client.get("/api/v1/tenant/billing/status")

    assert response.status_code == 200
    data = response.json()
    assert data["billing_status"] == "active"
    assert data["stripe_customer_id"] == "cus_mock_123"
