"""
Tests for LiteLLM summarizer.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from sentineldb.core.enums import RCAStrength
from sentineldb.core.models import CandidateCause
from sentineldb.llm.summarizer import LLMSummarizer


@pytest.fixture
def summarizer() -> LLMSummarizer:
    return LLMSummarizer()


@pytest.fixture
def dummy_cause() -> CandidateCause:
    return CandidateCause(
        cause_type="connection_saturation",
        rca_strength=RCAStrength.High,
        why_most_likely=["Active connections near max"],
    )


def test_no_api_key_returns_none(
    summarizer: LLMSummarizer, dummy_cause: CandidateCause, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    # The summarizer checks settings.GOOGLE_API_KEY, so we mock that too
    with patch("sentineldb.llm.summarizer.settings") as mock_settings:
        mock_settings.GOOGLE_API_KEY = ""
        result = summarizer.summarize(dummy_cause, "100 active connections")
    assert result is None


def test_mocked_litellm_returns_string(
    summarizer: LLMSummarizer, dummy_cause: CandidateCause
) -> None:
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[
        0
    ].message.content = "Connection pool is saturated. Please increase max_connections."

    with (
        patch("sentineldb.llm.summarizer.litellm.completion", return_value=mock_response),
        patch("sentineldb.llm.summarizer.settings") as mock_settings,
    ):
        mock_settings.GOOGLE_API_KEY = "dummy"
        mock_settings.LITELLM_MODEL = "gemini/gemini-2.5-flash-lite"
        result = summarizer.summarize(dummy_cause, "100 active connections")

    assert result == "Connection pool is saturated. Please increase max_connections."


def test_litellm_exception_returns_none(
    summarizer: LLMSummarizer, dummy_cause: CandidateCause
) -> None:
    with (
        patch("sentineldb.llm.summarizer.litellm.completion", side_effect=Exception("API down")),
        patch("sentineldb.llm.summarizer.settings") as mock_settings,
    ):
        mock_settings.GOOGLE_API_KEY = "dummy"
        result = summarizer.summarize(dummy_cause, "100 active connections")

    assert result is None


# ---------------------------------------------------------------------------
# PII Scrubbing Tests
# ---------------------------------------------------------------------------


def test_scrub_pii_hostnames(summarizer: LLMSummarizer) -> None:
    text = "host=db.internal and secondary=replica1.local also db.rds.amazonaws.com and custom=db.corp.example.com"
    scrubbed = summarizer._scrub_pii(text)
    assert "<host>" in scrubbed
    assert "db.internal" not in scrubbed
    assert "replica1.local" not in scrubbed
    assert "db.rds.amazonaws.com" not in scrubbed
    assert "db.corp.example.com" not in scrubbed


def test_scrub_pii_ipv4(summarizer: LLMSummarizer) -> None:
    text = "Connecting to 192.168.1.100 and 10.0.0.5."
    scrubbed = summarizer._scrub_pii(text)
    assert "<ip>" in scrubbed
    assert "192.168.1.100" not in scrubbed
    assert "10.0.0.5" not in scrubbed


def test_scrub_pii_usernames(summarizer: LLMSummarizer) -> None:
    text = "user=sentinel_ro, password=foo (user=root)"
    scrubbed = summarizer._scrub_pii(text)
    assert "<user>" in scrubbed
    assert "sentinel_ro" not in scrubbed
    assert "root" not in scrubbed


def test_scrub_pii_sql_literals(summarizer: LLMSummarizer) -> None:
    text = "query: SELECT * FROM users WHERE email='akash@example.com' AND id = 42"
    scrubbed = summarizer._scrub_pii(text)
    assert "<query>" in scrubbed
    assert "akash@example.com" not in scrubbed
    assert "42" not in scrubbed
