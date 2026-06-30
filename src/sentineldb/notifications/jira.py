"""Jira notification handler."""

from __future__ import annotations

import logging
import os

import httpx

from sentineldb.core.models import IncidentReport
from sentineldb.notifications.models import NotificationHandler

logger = logging.getLogger(__name__)


class JiraHandler(NotificationHandler):
    """Creates an incident ticket in Jira."""

    def __init__(self) -> None:
        self.webhook_url = os.environ.get("JIRA_WEBHOOK_URL")

    def notify(self, report: IncidentReport) -> None:
        """Create a Jira ticket via webhook or REST API."""
        if not self.webhook_url:
            logger.debug("JIRA_WEBHOOK_URL not set; skipping Jira notification.")
            return

        payload = {
            "fields": {
                "summary": f"DB Incident: {report.incident_id}",
                "description": f"Root Cause:\n{report.root_cause_summary}\n\nStrength: {report.rca_strength.value}",
                "issuetype": {"name": "Incident"},
                "project": {"key": os.environ.get("JIRA_PROJECT_KEY", "DBA")},
            }
        }

        try:
            response = httpx.post(self.webhook_url, json=payload, timeout=5.0)
            response.raise_for_status()
            logger.info("Successfully created Jira ticket for incident %s", report.incident_id)
        except Exception as e:
            logger.warning("Failed to create Jira ticket for incident %s: %s", report.incident_id, e)
