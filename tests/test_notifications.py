"""
Tests for notification dispatcher and handlers.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from sentineldb.core.enums import RCAStrength
from sentineldb.core.models import IncidentReport
from sentineldb.notifications.dispatcher import NotificationDispatcher
from sentineldb.notifications.freshdesk import FreshdeskHandler
from sentineldb.notifications.jira import JiraHandler
from sentineldb.notifications.slack import SlackHandler


@pytest.fixture
def sample_report() -> IncidentReport:
    return IncidentReport(
        incident_id="test-incident-uuid",
        rca_strength=RCAStrength.High,
        root_cause_summary="The database is unreachable.",
        why_most_likely=["All checks failed"],
        evidence=[],
    )


def test_slack_handler_sends_notification(sample_report: IncidentReport) -> None:
    with patch.dict("os.environ", {"SLACK_WEBHOOK_URL": "http://mock.slack.com/webhook"}):
        handler = SlackHandler()
        with patch("sentineldb.notifications.slack.httpx.post") as mock_post:
            mock_post.return_value.status_code = 200
            handler.notify(sample_report)

            mock_post.assert_called_once()
            args, kwargs = mock_post.call_args
            assert args[0] == "http://mock.slack.com/webhook"
            assert "blocks" in kwargs["json"]
            assert kwargs["timeout"] == 5.0


def test_slack_handler_skips_if_url_not_set(sample_report: IncidentReport) -> None:
    with patch.dict("os.environ", {}, clear=True):
        handler = SlackHandler()
        with patch("sentineldb.notifications.slack.httpx.post") as mock_post:
            handler.notify(sample_report)
            mock_post.assert_not_called()


def test_jira_handler_sends_notification(sample_report: IncidentReport) -> None:
    with patch.dict(
        "os.environ",
        {"JIRA_WEBHOOK_URL": "http://mock.jira.com/webhook", "JIRA_PROJECT_KEY": "OPS"},
    ):
        handler = JiraHandler()
        with patch("sentineldb.notifications.jira.httpx.post") as mock_post:
            mock_post.return_value.status_code = 200
            handler.notify(sample_report)

            mock_post.assert_called_once()
            args, kwargs = mock_post.call_args
            assert args[0] == "http://mock.jira.com/webhook"
            assert kwargs["json"]["fields"]["project"]["key"] == "OPS"


@pytest.mark.asyncio
async def test_freshdesk_handler_sends_notification(sample_report: IncidentReport) -> None:
    with patch.dict(
        "os.environ",
        {"FRESHDESK_DOMAIN": "mockdomain", "FRESHDESK_API_KEY": "mockkey"},
    ):
        handler = FreshdeskHandler()

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch(
            "sentineldb.notifications.freshdesk.httpx.AsyncClient", return_value=mock_client
        ):
            await handler.notify(sample_report)

        mock_client.post.assert_called_once()
        args, kwargs = mock_client.post.call_args
        assert args[0] == "https://mockdomain.freshdesk.com/api/v2/tickets"
        assert kwargs["auth"] == ("mockkey", "X")
        assert kwargs["json"]["priority"] == 2


def test_dispatcher_calls_all_handlers(sample_report: IncidentReport) -> None:
    dispatcher = NotificationDispatcher()

    mock_slack = MagicMock(spec=SlackHandler)
    mock_jira = MagicMock(spec=JiraHandler)
    dispatcher.handlers = [mock_slack, mock_jira]

    dispatcher.dispatch(sample_report)

    mock_slack.notify.assert_called_once_with(sample_report)
    mock_jira.notify.assert_called_once_with(sample_report)


def test_dispatcher_handles_exceptions(sample_report: IncidentReport) -> None:
    dispatcher = NotificationDispatcher()

    mock_slack = MagicMock(spec=SlackHandler)
    mock_slack.notify.side_effect = httpx.TimeoutException("Timeout")
    mock_jira = MagicMock(spec=JiraHandler)

    dispatcher.handlers = [mock_slack, mock_jira]

    # Should not raise exception
    dispatcher.dispatch(sample_report)

    mock_slack.notify.assert_called_once()
    mock_jira.notify.assert_called_once()
