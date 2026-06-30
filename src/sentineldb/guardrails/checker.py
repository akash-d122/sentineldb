"""
GuardrailChecker — allowlist-first SQL safety checker.

Strategy:
1. Normalise whitespace and strip the input SQL.
2. Check against the engine-specific allowlist (exact match).
   - Match  → allowed immediately; no further parsing needed.
   - No match → blocked immediately; sqlparse is then used only to
     determine *which* blocked pattern fired (for logging/auditing).

The LLM must never generate SQL that reaches this checker's execution path.
All SQL executed against monitored databases must pass this check first.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import sqlparse
import sqlparse.sql
import sqlparse.tokens as T

from sentineldb.guardrails.catalog import MYSQL_CATALOG, POSTGRES_CATALOG


def _normalise(sql: str) -> str:
    """Collapse whitespace and strip; case-sensitive for allowlist matching."""
    return re.sub(r"\s+", " ", sql.strip())


# Pre-compute normalised catalogs for fast exact-match lookup.
_PG_CATALOG_NORMALISED: frozenset[str] = frozenset(
    _normalise(sql) for sql in POSTGRES_CATALOG.values()
)

_MYSQL_CATALOG_NORMALISED: frozenset[str] = frozenset(
    _normalise(sql) for sql in MYSQL_CATALOG.values()
)


@dataclass(frozen=True)
class GuardrailResult:
    allowed: bool
    reason: str = ""
    blocked_pattern: str | None = None


# Blocked top-level statement types (sqlparse token classification).
_BLOCKED_STMT_TYPES = {
    "INSERT",
    "UPDATE",
    "DELETE",
    "TRUNCATE",
    "CREATE",
    "DROP",
    "ALTER",
    "RENAME",
    "GRANT",
    "REVOKE",
    "CALL",
}

# Regex guards for patterns sqlparse may miss or that need fast path.
_RE_COMMENT = re.compile(r"(--.*|/\*.*?\*/)", re.DOTALL)
_RE_SEMI = re.compile(r";")
_RE_SET_GLOBAL = re.compile(r"\bSET\s+GLOBAL\b", re.IGNORECASE)


class GuardrailChecker:
    """Allowlist-first SQL safety checker."""

    def check(self, sql: str, engine: str = "postgresql") -> GuardrailResult:
        """
        Return GuardrailResult.allowed=True only when sql is an exact catalog match for the given engine.
        All non-catalog SQL is rejected; sqlparse identifies the blocked pattern.
        """
        normalised = _normalise(sql)
        catalog = _PG_CATALOG_NORMALISED if engine == "postgresql" else _MYSQL_CATALOG_NORMALISED

        # ── Step 1: Allowlist check ──────────────────────────────────────────
        if normalised in catalog:
            return GuardrailResult(allowed=True)

        # ── Step 2: Not in catalog → blocked. Use sqlparse to name the pattern.
        blocked_pattern = self._identify_blocked_pattern(normalised, sql)
        return GuardrailResult(
            allowed=False,
            reason=f"SQL not in approved diagnostic catalog for engine '{engine}'. Blocked pattern: {blocked_pattern}",
            blocked_pattern=blocked_pattern,
        )

    # ------------------------------------------------------------------
    # Pattern identification (audit only — does not gate allow/deny)
    # ------------------------------------------------------------------

    def _identify_blocked_pattern(self, normalised: str, original: str) -> str:
        """Identify the highest-priority blocked pattern for audit logging."""

        # SQL comments present
        if _RE_COMMENT.search(original):
            return "comment_bypass"

        # Multi-statement (semicolon present anywhere)
        if _RE_SEMI.search(normalised):
            return "multi_statement"

        # SET GLOBAL
        if _RE_SET_GLOBAL.search(normalised):
            return "set_global"

        # Parse with sqlparse for statement type classification
        parsed = sqlparse.parse(normalised)
        if parsed:
            stmt = parsed[0]
            stmt_type = stmt.get_type()
            if stmt_type in _BLOCKED_STMT_TYPES:
                return stmt_type.lower()

            # Check for CALL (sqlparse may return None for some dialects)
            first_keyword = self._first_keyword(stmt)
            if first_keyword in _BLOCKED_STMT_TYPES:
                return first_keyword.lower()

        return "not_in_catalog"

    @staticmethod
    def _first_keyword(stmt: sqlparse.sql.Statement) -> str:
        """Return the uppercased first keyword token in the statement."""
        for token in stmt.flatten():
            if token.ttype in (T.Keyword, T.Keyword.DDL, T.Keyword.DML):
                return token.normalized.upper()
        return ""
