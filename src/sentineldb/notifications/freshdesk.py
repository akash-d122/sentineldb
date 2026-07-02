"""Freshdesk notification handler."""

from __future__ import annotations

import logging
import os

import httpx

from sentineldb.core.models import IncidentReport
from sentineldb.notifications.models import NotificationHandler

logger = logging.getLogger(__name__)


class FreshdeskHandler(NotificationHandler):
    """Creates a ticket in Freshdesk."""

    def __init__(self) -> None:
        self.domain = os.environ.get("FRESHDESK_DOMAIN")
        self.api_key = os.environ.get("FRESHDESK_API_KEY")

    async def notify(self, report: IncidentReport) -> None:
        """Create a Freshdesk ticket via REST API."""
        if not self.domain or not self.api_key:
            logger.debug(
                "FRESHDESK_DOMAIN or FRESHDESK_API_KEY not set; skipping Freshdesk notification."
            )
            return

        url = f"https://{self.domain}.freshdesk.com/api/v2/tickets"

        payload = {
            "description": f"Root Cause:<br>{report.root_cause_summary}<br><br>Strength: {report.rca_strength.value}",
            "subject": f"DB Incident: {report.incident_id}",
            "email": os.environ.get("FRESHDESK_DEFAULT_EMAIL", "alerts@sentineldb.local"),
            "priority": 2,  # Medium
            "status": 2,  # Open
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url, json=payload, auth=(self.api_key, "X"), timeout=5.0
                )
            response.raise_for_status()
            logger.info("Successfully created Freshdesk ticket for incident %s", report.incident_id)
        except Exception as e:
            logger.warning(
                "Failed to create Freshdesk ticket for incident %s: %s", report.incident_id, e
            )
