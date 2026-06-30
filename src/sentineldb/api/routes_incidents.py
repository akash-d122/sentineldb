from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

import yaml
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from sentineldb.core.enums import AlertType, IncidentStatus, Severity
from sentineldb.core.models import AlertPayload
from sentineldb.db.models import IncidentORM, IncidentReportORM
from sentineldb.db.session import get_session
from sentineldb.worker.tasks import run_incident_analysis

router = APIRouter(prefix="/api/v1/incidents", tags=["incidents"])


class IncidentResponse(BaseModel):
    incident_id: uuid.UUID
    instance_id: str
    alert_type: str
    severity: str
    metric_value: float | None
    threshold_value: float | None
    triggered_at: datetime
    status: str
    created_at: datetime


class ManualTriggerRequest(BaseModel):
    instance_id: str
    alert_type: AlertType
    severity: Severity = Severity.P3
    metric_value: float | None = None
    threshold_value: float | None = None


def _load_registry() -> dict[str, dict]:
    try:
        with open("instances.yaml") as f:
            data = yaml.safe_load(f)
            return data.get("instances", {})
    except Exception:
        return {}


@router.get("", response_model=list[IncidentResponse])
async def list_incidents(
    skip: int = 0,
    limit: int = 100,
    status: IncidentStatus | None = None,
    instance_id: str | None = None,
    session: AsyncSession = Depends(get_session),
) -> Any:
    """Get a list of incidents, optionally filtered."""
    stmt = select(IncidentORM).order_by(desc(IncidentORM.created_at)).offset(skip).limit(limit)
    if status:
        stmt = stmt.where(IncidentORM.status == status.value)
    if instance_id:
        stmt = stmt.where(IncidentORM.instance_id == instance_id)

    result = await session.execute(stmt)
    incidents = result.scalars().all()
    return incidents


@router.get("/{incident_id}", response_model=IncidentResponse)
async def get_incident(incident_id: uuid.UUID, session: AsyncSession = Depends(get_session)) -> Any:
    """Get a single incident by ID."""
    stmt = select(IncidentORM).where(IncidentORM.incident_id == incident_id)
    result = await session.execute(stmt)
    incident = result.scalars().first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@router.get("/{incident_id}/report")
async def get_incident_report(
    incident_id: uuid.UUID, session: AsyncSession = Depends(get_session)
) -> Any:
    """Get the RCA report for an incident. Returns 202 if not yet ready."""
    # First check if incident exists and its status
    stmt = select(IncidentORM).where(IncidentORM.incident_id == incident_id)
    result = await session.execute(stmt)
    incident = result.scalars().first()

    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    from fastapi.responses import JSONResponse

    if incident.status in (
        IncidentStatus.queued.value,
        IncidentStatus.collecting.value,
        IncidentStatus.analyzing.value,
    ):
        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content={
                "status": "accepted",
                "message": f"Incident analysis in progress (status: {incident.status})",
            },
        )
    if incident.status == IncidentStatus.failed.value:
        raise HTTPException(status_code=500, detail="Incident analysis failed")

    # If report_ready, fetch the report
    stmt_report = select(IncidentReportORM).where(IncidentReportORM.incident_id == incident_id)
    res_report = await session.execute(stmt_report)
    report = res_report.scalars().first()

    if not report:
        # Should not happen if status is report_ready, but handle safely
        raise HTTPException(status_code=404, detail="Report not found for incident")

    return {
        "report_id": str(report.report_id),
        "incident_id": str(report.incident_id),
        "rca_strength": report.rca_strength,
        "root_cause_summary": report.root_cause_summary,
        "why_most_likely": report.why_most_likely,
        "evidence": report.evidence,
        "runbook_reference": report.runbook_reference,
        "safe_next_actions": report.safe_next_actions,
        "requires_approval": report.requires_approval,
        "missing_evidence": report.missing_evidence,
        "llm_used": report.llm_used,
        "generated_at": report.generated_at,
    }


@router.post("/analyze", status_code=status.HTTP_202_ACCEPTED)
async def trigger_manual_analysis(
    req: ManualTriggerRequest, session: AsyncSession = Depends(get_session)
) -> Any:
    """Manually trigger an incident analysis."""
    registry = _load_registry()
    if req.instance_id not in registry:
        raise HTTPException(status_code=400, detail=f"INSTANCE_NOT_REGISTERED: {req.instance_id}")

    # Build an AlertPayload structure
    payload = AlertPayload(
        instance_id=req.instance_id,
        alert_type=req.alert_type,
        severity=req.severity,
        metric_value=req.metric_value,
        threshold_value=req.threshold_value,
        raw_payload={"source": "manual_trigger"},
    )

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

    # Enqueue analysis
    run_incident_analysis.delay(incident_id_str, payload_dict)

    return {
        "status": "accepted",
        "incident_id": incident_id_str,
    }
