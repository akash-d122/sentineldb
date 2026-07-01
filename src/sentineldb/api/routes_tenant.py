"""
FastAPI router for tenant onboarding and billing endpoints.
"""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from sentineldb.api.dependencies import set_tenant_context, verify_jwt
from sentineldb.db.models import TenantORM, ThresholdConfigORM
from sentineldb.db.session import get_session, tenant_context
from sentineldb.services.billing import billing_service

router = APIRouter(
    prefix="/api/v1/tenant",
    tags=["tenant"],
    dependencies=[Depends(verify_jwt), Depends(set_tenant_context)],
)


class OnboardingRequest(BaseModel):
    name: str
    plan_tier: str = "free"


class OnboardingResponse(BaseModel):
    tenant_id: uuid.UUID
    name: str
    billing_status: str
    stripe_customer_id: str | None
    plan_tier: str


class BillingStatusResponse(BaseModel):
    tenant_id: uuid.UUID
    billing_status: str
    stripe_customer_id: str | None
    plan_tier: str


@router.post("/onboarding", response_model=OnboardingResponse, status_code=status.HTTP_201_CREATED)
async def onboard_tenant(
    req: OnboardingRequest, session: AsyncSession = Depends(get_session)
) -> Any:
    """
    Onboard a new tenant. Uses the tenant_id extracted from the JWT token.
    """
    tenant_id = tenant_context.get()
    if not tenant_id:
        raise HTTPException(status_code=500, detail="Missing tenant context")

    stmt = select(TenantORM).where(TenantORM.tenant_id == tenant_id)
    # Exclude tenant filter for fetching tenant object itself, since tenant filter
    # uses TenantMixin and TenantORM doesn't use it, but to be safe.
    result = await session.execute(stmt)
    existing = result.scalars().first()

    if existing:
        raise HTTPException(status_code=400, detail="Tenant already onboarded")

    stripe_customer_id = billing_service.provision_subscription(tenant_id, req.plan_tier)
    billing_status = billing_service.check_subscription_status(stripe_customer_id)

    new_tenant = TenantORM(
        tenant_id=tenant_id,
        name=req.name,
        billing_status=billing_status,
        stripe_customer_id=stripe_customer_id,
        plan_tier=req.plan_tier,
    )
    session.add(new_tenant)

    # Provision default thresholds for a generic 'default' instance
    default_threshold_1 = ThresholdConfigORM(
        instance_id="default",
        metric_name="cpu_utilization",
        warning_threshold=80.0,
        critical_threshold=90.0,
    )
    session.add(default_threshold_1)

    await session.commit()
    await session.refresh(new_tenant)

    return new_tenant


@router.get("/billing/status", response_model=BillingStatusResponse)
async def get_billing_status(session: AsyncSession = Depends(get_session)) -> Any:
    tenant_id = tenant_context.get()
    if not tenant_id:
        raise HTTPException(status_code=500, detail="Missing tenant context")

    stmt = select(TenantORM).where(TenantORM.tenant_id == tenant_id)
    result = await session.execute(stmt)
    tenant = result.scalars().first()

    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # Sync mock billing status
    current_status = billing_service.check_subscription_status(tenant.stripe_customer_id)
    if current_status != tenant.billing_status:
        tenant.billing_status = current_status
        await session.commit()
        await session.refresh(tenant)

    return tenant
