from __future__ import annotations

import json
from typing import Any

import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession

from sentineldb.core.config import settings
from sentineldb.core.models import AlertPayload
from sentineldb.db.models import IncidentORM
from sentineldb.worker.tasks import run_incident_analysis


async def create_and_analyze_incident(
    payload: AlertPayload,
    session: AsyncSession,
) -> dict[str, Any]:
    """Create an incident record and dispatch the analysis task."""
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
    payload_dict = payload.model_dump(mode="json")

    from sentineldb.db.session import tenant_context

    tid = tenant_context.get()
    tenant_id_str = str(tid) if tid else None

    run_incident_analysis.delay(incident_id_str, payload_dict, tenant_id_str)

    if tenant_id_str:
        try:
            r = redis.from_url(settings.REDIS_URL)
            event = {"incident_id": incident_id_str, "status": "queued", "tenant_id": tenant_id_str}
            await r.publish(f"incident_updates:{tenant_id_str}", json.dumps(event))
            await r.aclose()
        except Exception as e:
            import logging

            logging.getLogger(__name__).warning(f"Failed to publish to Redis: {e}")

    return {
        "status": "accepted",
        "incident_id": incident_id_str,
    }
