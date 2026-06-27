"""
LiteLLM summarizer with PII scrubbing and fallback path.
"""

from __future__ import annotations

import logging
import re

import litellm

from sentineldb.core.config import settings
from sentineldb.core.models import CandidateCause

logger = logging.getLogger(__name__)

# Widen regex to capture corporate domains, AWS RDS, etc.
# Looks for typical hostname shapes or explicit cloud domains.
_RE_HOSTNAME = re.compile(
    r"\b[a-zA-Z0-9.-]+\.(internal|local|compute\.amazonaws\.com|rds\.amazonaws\.com|corp\.[a-z]+\.com)\b",
    re.IGNORECASE,
)

# Standard IPv4
_RE_IPV4 = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")

# Simple heuristic for usernames in connection strings/logs
_RE_USER = re.compile(r"\buser(name)?=([a-zA-Z0-9_]+)\b", re.IGNORECASE)

# SQL literal heuristic: text in single quotes, or numbers after =/>/<
_RE_SQL_STRING = re.compile(r"'[^']*'")
_RE_SQL_NUMBER = re.compile(r"([=<>]+\s*)\d+\b")


class LLMSummarizer:
    """Uses LiteLLM to polish deterministic root cause summaries."""

    def summarize(self, cause: CandidateCause, evidence_summary: str) -> str | None:
        """
        Return a 1-3 sentence polished root cause summary, or None
        if the API key is missing or the call fails.
        """
        if not settings.GOOGLE_API_KEY:
            logger.debug("Skipping LLM summarizer: GOOGLE_API_KEY not set.")
            return None

        scrubbed_evidence = self._scrub_pii(evidence_summary)

        prompt = (
            f"You are a database incident analysis assistant.\n"
            f"Write a concise 1 to 3 sentence root cause summary for this incident.\n"
            f"Do not invent metrics. Use only the provided evidence.\n\n"
            f"Cause type: {cause.cause_type}\n"
            f"Evidence:\n{scrubbed_evidence}"
        )

        try:
            response = litellm.completion(
                model=settings.LITELLM_MODEL,
                messages=[{"role": "user", "content": prompt}],
                api_key=settings.GOOGLE_API_KEY,
                temperature=0.1,  # Low temp for deterministic-ish, factual summaries
                max_tokens=150,
            )
            content = response.choices[0].message.content
            if content:
                return content.strip()
            return None
        except Exception as e:
            logger.warning("LLM summarization failed, falling back to deterministic: %s", e)
            return None

    def _scrub_pii(self, text: str) -> str:
        """Replace hostnames, IPs, usernames, and SQL literals with placeholders."""
        text = _RE_HOSTNAME.sub("<host>", text)
        text = _RE_IPV4.sub("<ip>", text)

        # Replace the captured group (username) but keep 'user=' prefix
        text = _RE_USER.sub(r"\g<1>=<user>" if "name=" in text.lower() else "user=<user>", text)

        text = _RE_SQL_STRING.sub("'<query>'", text)
        text = _RE_SQL_NUMBER.sub(r"\g<1><query>", text)

        return text
