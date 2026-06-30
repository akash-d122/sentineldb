"""
API dependencies including Authentication and Multi-Tenancy.
"""

from __future__ import annotations

import logging
import os
import uuid
from collections.abc import AsyncGenerator
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient

from sentineldb.db.session import tenant_context

logger = logging.getLogger(__name__)

security = HTTPBearer()

# Default to a generic placeholder JWKS URL if not provided.
JWKS_URL = os.environ.get(
    "SUPABASE_JWKS_URL", "https://your-project-ref.supabase.co/rest/v1/jwks"
)
jwks_client = PyJWKClient(JWKS_URL)


def verify_jwt(credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]) -> dict:
    """
    Verify the JWT token from Supabase using JWKS.
    In local development, if ENV != production, we might allow a fallback.
    Returns the parsed payload.
    """
    token = credentials.credentials
    auth_enforced = os.environ.get("AUTH_ENFORCED", "true").lower() == "true"

    if not auth_enforced and token == "dev-token":
        # Allow dev token bypass
        return {"sub": "dev-user-id", "tenant_id": "00000000-0000-0000-0000-000000000000"}

    try:
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        # We allow a broad audience or configure it via env for real production
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            options={"verify_aud": False},
        )
        return payload
    except jwt.PyJWKClientError as e:
        logger.error("Failed to fetch JWKS: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify identity provider keys",
        )
    except jwt.InvalidTokenError as e:
        logger.warning("Invalid JWT: %s", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.warning("JWT validation failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def set_tenant_context(
    payload: Annotated[dict, Depends(verify_jwt)],
) -> AsyncGenerator[uuid.UUID, None]:
    """
    Extract tenant_id from the verified JWT payload and set it in contextvars.
    """
    tenant_id_str = payload.get("tenant_id")
    if not tenant_id_str:
        # Fallback to 'sub' or raise if multi-tenancy is strictly required.
        tenant_id_str = payload.get("sub")

    if not tenant_id_str:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Missing tenant context in token",
        )

    try:
        tenant_id = uuid.UUID(tenant_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid tenant ID format",
        )

    token = tenant_context.set(tenant_id)
    try:
        yield tenant_id
    finally:
        tenant_context.reset(token)

