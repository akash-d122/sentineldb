"""Notification dispatcher."""

from __future__ import annotations

import logging

from sentineldb.core.models import IncidentReport
from sentineldb.notifications.freshdesk import FreshdeskHandler
from sentineldb.notifications.jira import JiraHandler
from sentineldb.notifications.models import NotificationHandler
from sentineldb.notifications.slack import SlackHandler

logger = logging.getLogger(__name__)


class NotificationDispatcher:
    """Dispatches notifications to all configured handlers."""

    def __init__(self) -> None:
        self.handlers: list[NotificationHandler] = [
            SlackHandler(),
            JiraHandler(),
            FreshdeskHandler(),
        ]

    async def dispatch(self, report: IncidentReport) -> None:
        """Send notifications using all handlers. Catch and log individual failures."""
        logger.info("Dispatching notifications for incident %s", report.incident_id)
        import asyncio

        async def _safe_notify(h):
            try:
                await h.notify(report)
            except Exception as e:
                logger.error("Notification handler %s failed: %s", h.__class__.__name__, e)

        await asyncio.gather(*(_safe_notify(h) for h in self.handlers))
