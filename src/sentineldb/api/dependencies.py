"""
API dependencies including Authentication.
"""

from __future__ import annotations

import logging
import os
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

logger = logging.getLogger(__name__)

security = HTTPBearer()

def verify_jwt(credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]) -> str:
    """
    Verify the JWT token from Supabase/Auth0.
    In local development, if ENV != production, we might allow a fallback.
    """
    token = credentials.credentials

    # Check if Auth is strictly enforced (default yes in V2)
    auth_enforced = os.environ.get("AUTH_ENFORCED", "true").lower() == "true"

    if not auth_enforced and token == "dev-token":
        # Allow dev token bypass
        return "dev-user-id"

    # TODO: Implement real JWKS verification for Supabase/Auth0 here.
    # For the scope of V2 demo, we ensure the token format is basic JWT.
    import base64
    try:
        header, payload, signature = token.split(".")
        # Just simple structure check for now to avoid pulling heavy cryptography libs
        # until the exact provider (Auth0 vs Supabase) is finalized by the infra team.
        base64.urlsafe_b64decode(header + "==")
        base64.urlsafe_b64decode(payload + "==")
        return "authenticated-user-id"
    except Exception:
        logger.warning("Invalid JWT structure received.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
