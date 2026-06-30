from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

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
    run_incident_analysis.delay(incident_id_str, payload_dict)

    return {
        "status": "accepted",
        "incident_id": incident_id_str,
    }
