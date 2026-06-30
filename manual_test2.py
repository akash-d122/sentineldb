import base64
import os
from unittest.mock import AsyncMock, MagicMock

from fastapi.testclient import TestClient

from sentineldb.api.main import app
from sentineldb.db.session import get_session

os.environ["AUTH_ENFORCED"] = "true"

mock_session = AsyncMock()
app.dependency_overrides[get_session] = lambda: mock_session

client = TestClient(app)

# Dummy JWT: header.payload.signature
dummy_header = base64.urlsafe_b64encode(b'{"alg":"HS256","typ":"JWT"}').decode().rstrip("=")
dummy_payload = base64.urlsafe_b64encode(b'{"sub":"1234567890","name":"John Doe","iat":1516239022}').decode().rstrip("=")
dummy_jwt = f"{dummy_header}.{dummy_payload}.signature"

print("--- Testing Authenticated Request (Dummy JWT, AUTH_ENFORCED=true) ---")
mock_result = MagicMock()
mock_result.scalars.return_value.all.return_value = []
mock_session.execute.return_value = mock_result

res = client.get("/api/v1/config/thresholds", headers={"Authorization": f"Bearer {dummy_jwt}"})
print(f"Status: {res.status_code} (Expected 200)")
print(f"Response: {res.json()}\n")
