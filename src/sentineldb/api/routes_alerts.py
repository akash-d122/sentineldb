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
from sentineldb.db.models import IncidentORM
from sentineldb.db.session import get_session
from sentineldb.worker.tasks import run_incident_analysis

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

    # 1. Create Incident record
    incident = IncidentORM(
        instance_id=payload.instance_id,
        alert_type=payload.alert_type.value,
        severity=payload.severity.value,
        metric_value=payload.metric_value,
        threshold_value=payload.threshold_value,
        triggered_at=payload.triggered_at,
        status="queued",
        raw_payload=payload.raw_payload,
    )
    session.add(incident)
    await session.commit()
    await session.refresh(incident)

    incident_id_str = str(incident.incident_id)

    # 2. Dispatch Celery task
    # We must serialize the Pydantic model to a JSON-safe dict,
    # as raw datetime/UUID objects will break JSON serialization (R2).
    payload_dict = payload.model_dump(mode="json")
    run_incident_analysis.delay(incident_id_str, payload_dict)

    return {
        "status": "accepted",
        "incident_id": incident_id_str,
    }
