import asyncio
from fastapi.testclient import TestClient
from sentineldb.api.main import app
from sentineldb.api.dependencies import verify_jwt
from sentineldb.db.session import get_session
from unittest.mock import AsyncMock, MagicMock

# 1. Mock DB Session
mock_session = AsyncMock()
app.dependency_overrides[get_session] = lambda: mock_session

# 2. Test Auth Without Token
client = TestClient(app)
print("--- 1. Testing Unauthenticated Request ---")
res = client.get("/api/v1/config/thresholds")
print(f"Status: {res.status_code} (Expected 403 or 401)")
print(f"Response: {res.json()}\n")

# 3. Test Auth With dev-token
print("--- 2. Testing Authenticated Request (dev-token) ---")
mock_result = MagicMock()
mock_result.scalars.return_value.all.return_value = []
mock_session.execute.return_value = mock_result

res = client.get("/api/v1/config/thresholds", headers={"Authorization": "Bearer dev-token"})
print(f"Status: {res.status_code} (Expected 200)")
print(f"Response: {res.json()}\n")

# 4. Test Create Threshold
print("--- 3. Testing Create Threshold ---")
mock_result_first = MagicMock()
mock_result_first.scalars.return_value.first.return_value = None
mock_session.execute.return_value = mock_result_first

payload = {
    "instance_id": "demo-instance",
    "metric_name": "cloudwatch_cpu",
    "warning_threshold": 75.5,
    "critical_threshold": 90.0
}
res = client.post("/api/v1/config/thresholds", json=payload, headers={"Authorization": "Bearer dev-token"})
print(f"Status: {res.status_code} (Expected 201)")
print(f"Response: {res.json()}\n")

