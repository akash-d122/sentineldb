"""
Mock Billing service (Stripe Mock).
"""
from __future__ import annotations

import logging
import uuid
from typing import Literal

logger = logging.getLogger(__name__)

class StripeMockService:
    @staticmethod
    def provision_subscription(tenant_id: uuid.UUID, plan_tier: str) -> str:
        """
        Mock provisioning a Stripe subscription.
        Returns a mock Stripe customer ID.
        """
        logger.info(f"Provisioning {plan_tier} subscription for tenant {tenant_id}")
        return f"cus_mock_{tenant_id.hex[:10]}"

    @staticmethod
    def check_subscription_status(stripe_customer_id: str | None) -> Literal["active", "past_due", "canceled", "incomplete"]:
        """
        Mock checking subscription status.
        In reality, this would query the Stripe API.
        """
        if not stripe_customer_id:
            return "incomplete"
        # For mock purposes, just return active
        return "active"

billing_service = StripeMockService()
