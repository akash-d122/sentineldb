"""
FastAPI router for configuration endpoints (Threshold UI).
"""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from sentineldb.db.models import ThresholdConfigORM
from sentineldb.db.session import get_session

router = APIRouter(
    prefix="/api/v1/config/thresholds",
    tags=["config"],
)


class ThresholdConfigSchema(BaseModel):
    instance_id: str
    metric_name: str
    warning_threshold: float
    critical_threshold: float


class ThresholdConfigResponse(ThresholdConfigSchema):
    id: uuid.UUID


@router.get("", response_model=list[ThresholdConfigResponse])
async def list_thresholds(
    instance_id: str | None = None, session: AsyncSession = Depends(get_session)
) -> Any:
    stmt = select(ThresholdConfigORM)
    if instance_id:
        stmt = stmt.where(ThresholdConfigORM.instance_id == instance_id)

    result = await session.execute(stmt)
    return result.scalars().all()


@router.post("", response_model=ThresholdConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_or_update_threshold(
    payload: ThresholdConfigSchema, session: AsyncSession = Depends(get_session)
) -> Any:
    stmt = select(ThresholdConfigORM).where(
        ThresholdConfigORM.instance_id == payload.instance_id,
        ThresholdConfigORM.metric_name == payload.metric_name,
    )
    result = await session.execute(stmt)
    existing = result.scalars().first()

    if existing:
        existing.warning_threshold = payload.warning_threshold
        existing.critical_threshold = payload.critical_threshold
        await session.commit()
        await session.refresh(existing)
        return existing

    new_config = ThresholdConfigORM(
        id=uuid.uuid4(),
        instance_id=payload.instance_id,
        metric_name=payload.metric_name,
        warning_threshold=payload.warning_threshold,
        critical_threshold=payload.critical_threshold,
    )
    session.add(new_config)
    await session.commit()
    await session.refresh(new_config)
    return new_config


@router.delete("/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_threshold(
    config_id: uuid.UUID, session: AsyncSession = Depends(get_session)
) -> None:
    config = await session.get(ThresholdConfigORM, config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Threshold configuration not found")

    await session.delete(config)
    await session.commit()
