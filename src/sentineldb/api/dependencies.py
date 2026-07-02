"""
API dependencies including Authentication and Multi-Tenancy.
"""

from __future__ import annotations

import logging
import os
import time
import uuid
from collections.abc import AsyncGenerator
from typing import Annotated

import httpx
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from sentineldb.db.session import tenant_context

logger = logging.getLogger(__name__)

security = HTTPBearer()

# Default to a generic placeholder JWKS URL if not provided.
JWKS_URL = os.environ.get("SUPABASE_JWKS_URL", "https://your-project-ref.supabase.co/rest/v1/jwks")

# Optional audience configuration (e.g. for Supabase typical setup)
SUPABASE_AUDIENCE = os.environ.get("SUPABASE_AUDIENCE", "authenticated")

# Async JWKS caching
_jwks_cache = None
_jwks_cache_time = 0
JWKS_CACHE_TTL = 3600


async def get_jwks(force_refresh: bool = False) -> dict:
    global _jwks_cache, _jwks_cache_time
    if not force_refresh and _jwks_cache and time.time() - _jwks_cache_time < JWKS_CACHE_TTL:
        return _jwks_cache

    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.get(JWKS_URL)
        resp.raise_for_status()
        _jwks_cache = resp.json()
        _jwks_cache_time = time.time()
        return _jwks_cache


async def get_signing_key(token: str):
    unverified_header = jwt.get_unverified_header(token)
    kid = unverified_header.get("kid")
    if not kid:
        raise jwt.InvalidTokenError("Missing kid in token header")

    jwks = await get_jwks()

    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            return jwt.algorithms.RSAAlgorithm.from_jwk(key)

    # Key not found, could be rotated. Force refresh and try again.
    jwks = await get_jwks(force_refresh=True)
    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            return jwt.algorithms.RSAAlgorithm.from_jwk(key)

    raise jwt.InvalidTokenError(f"Unable to find appropriate key for kid: {kid}")


async def verify_jwt(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
) -> dict:
    """
    Verify the JWT token from Supabase using JWKS asynchronously.
    In local development, if ENV != production, we might allow a fallback.
    Returns the parsed payload.
    """
    token = credentials.credentials
    auth_enforced = os.environ.get("AUTH_ENFORCED", "true").lower() == "true"

    if not auth_enforced and token == "dev-token":
        # Allow dev token bypass
        return {"sub": "dev-user-id", "tenant_id": "00000000-0000-0000-0000-000000000000"}

    try:
        signing_key = await get_signing_key(token)
        # We enforce audience validation to prevent token reuse
        payload = jwt.decode(
            token,
            signing_key,
            algorithms=["RS256"],
            audience=SUPABASE_AUDIENCE,
            options={"verify_aud": True},
        )
        return payload
    except httpx.HTTPError as e:
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
