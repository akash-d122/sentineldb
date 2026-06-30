"""Slack notification handler."""

from __future__ import annotations

import logging
import os

import httpx

from sentineldb.core.models import IncidentReport
from sentineldb.notifications.models import NotificationHandler

logger = logging.getLogger(__name__)


class SlackHandler(NotificationHandler):
    """Sends incident reports to a Slack webhook."""

    def __init__(self) -> None:
        self.webhook_url = os.environ.get("SLACK_WEBHOOK_URL")

    def notify(self, report: IncidentReport) -> None:
        """Send a formatted Slack message synchronously."""
        if not self.webhook_url:
            logger.debug("SLACK_WEBHOOK_URL not set; skipping Slack notification.")
            return

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"🚨 Database Incident: {report.incident_id}",
                    "emoji": True,
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Root Cause:*\n{report.root_cause_summary}",
                },
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*RCA Strength:*\n{report.rca_strength.value}",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*LLM Used:*\n{'Yes' if report.llm_used else 'No'}",
                    },
                ],
            },
        ]

        if report.safe_next_actions:
            actions_text = "\n".join(
                f"- {a.label}: {a.description}" for a in report.safe_next_actions
            )
            blocks.append(
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Safe Next Actions:*\n{actions_text}",
                    },
                }
            )

        payload = {"blocks": blocks}

        try:
            # Synchronous httpx post since we are in a Celery task that is already running
            # inside an async loop wrapper if invoked from `run_incident_analysis`,
            # or in a normal sync thread if run from a dedicated notification task.
            # Actually, `httpx.post` is sync.
            response = httpx.post(self.webhook_url, json=payload, timeout=5.0)
            response.raise_for_status()
            logger.info("Successfully sent Slack notification for incident %s", report.incident_id)
        except Exception as e:
            logger.warning(
                "Failed to send Slack notification for incident %s: %s", report.incident_id, e
            )
