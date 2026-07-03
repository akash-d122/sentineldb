"""Models for notification dispatch."""

from __future__ import annotations

import abc

from sentineldb.core.models import IncidentReport


class NotificationHandler(abc.ABC):
    """Abstract base class for notification handlers."""

    @abc.abstractmethod
    async def notify(self, report: IncidentReport) -> None:
        """Dispatch a notification for the given incident report."""
        pass
