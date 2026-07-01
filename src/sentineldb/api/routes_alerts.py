"""
FastAPI router for incoming alerts.
"""

from __future__ import annotations

import hashlib
import hmac
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from sentineldb.core.config import settings
from sentineldb.core.models import AlertPayload
from sentineldb.db.session import get_session

router = APIRouter(prefix="/api/v1/alerts", tags=["alerts"])


async def verify_webhook_signature(
    request: Request,
    x_webhook_signature: str | None = Header(default=None),
) -> None:
    """
    Verify the HMAC-SHA256 signature of the incoming webhook payload.
    Skips validation in development if WEBHOOK_SECRET is not configured.
    Raises RuntimeError on startup/first request if in production.
    """
    if not settings.WEBHOOK_SECRET:
        if settings.ENV == "production":
            raise RuntimeError("WEBHOOK_SECRET is required in production environment.")
        # Development fallback
        import logging

        logging.getLogger(__name__).warning(
            "WEBHOOK_SECRET not set, skipping signature validation."
        )
        return

    if not x_webhook_signature:
        raise HTTPException(status_code=401, detail="Missing X-Webhook-Signature header")

    body = await request.body()
    expected_mac = hmac.new(
        settings.WEBHOOK_SECRET.encode("utf-8"), body, hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected_mac, x_webhook_signature):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")


import uuid

from sentineldb.db.session import tenant_context
from sentineldb.services.incident import create_and_analyze_incident


@router.post(
    "/inbound",
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(verify_webhook_signature)],
)
async def ingest_alert(
    payload: AlertPayload,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Ingest a new alert, persist it, and dispatch background analysis."""
    # Set the tenant context from the payload, fallback to the default migration tenant
    tid = payload.tenant_id or uuid.UUID("00000000-0000-0000-0000-000000000000")
    token = tenant_context.set(tid)
    try:
        return await create_and_analyze_incident(payload, session)
    finally:
        tenant_context.reset(token)
