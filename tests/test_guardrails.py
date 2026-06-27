"""
Tests for GuardrailChecker — all blocked patterns must be covered before implementation.
Run: uv run pytest tests/test_guardrails.py
"""
import pytest

from sentineldb.guardrails.checker import GuardrailChecker, GuardrailResult
from sentineldb.guardrails.catalog import DIAGNOSTIC_CATALOG


@pytest.fixture
def checker() -> GuardrailChecker:
    return GuardrailChecker()


# ---------------------------------------------------------------------------
# Allowed paths
# ---------------------------------------------------------------------------


def test_exact_catalog_match_allowed(checker: GuardrailChecker) -> None:
    sql = next(iter(DIAGNOSTIC_CATALOG.values()))
    result = checker.check(sql)
    assert result.allowed is True, f"Expected catalog SQL to be allowed: {result.reason}"


def test_all_catalog_entries_allowed(checker: GuardrailChecker) -> None:
    for name, sql in DIAGNOSTIC_CATALOG.items():
        result = checker.check(sql)
        assert result.allowed is True, f"Catalog entry '{name}' blocked: {result.reason}"


# ---------------------------------------------------------------------------
# DML — blocked
# ---------------------------------------------------------------------------


def test_insert_blocked(checker: GuardrailChecker) -> None:
    result = checker.check("INSERT INTO foo VALUES (1)")
    assert result.allowed is False
    assert result.blocked_pattern is not None


def test_update_blocked(checker: GuardrailChecker) -> None:
    result = checker.check("UPDATE foo SET x=1")
    assert result.allowed is False


def test_delete_blocked(checker: GuardrailChecker) -> None:
    result = checker.check("DELETE FROM foo")
    assert result.allowed is False


def test_truncate_blocked(checker: GuardrailChecker) -> None:
    result = checker.check("TRUNCATE TABLE foo")
    assert result.allowed is False


# ---------------------------------------------------------------------------
# DDL — blocked
# ---------------------------------------------------------------------------


def test_create_table_blocked(checker: GuardrailChecker) -> None:
    result = checker.check("CREATE TABLE foo (id INT)")
    assert result.allowed is False


def test_drop_table_blocked(checker: GuardrailChecker) -> None:
    result = checker.check("DROP TABLE foo")
    assert result.allowed is False


def test_alter_table_blocked(checker: GuardrailChecker) -> None:
    result = checker.check("ALTER TABLE foo ADD COLUMN x INT")
    assert result.allowed is False


# ---------------------------------------------------------------------------
# GRANT / REVOKE — blocked
# ---------------------------------------------------------------------------


def test_grant_blocked(checker: GuardrailChecker) -> None:
    result = checker.check("GRANT SELECT ON foo TO user")
    assert result.allowed is False


def test_revoke_blocked(checker: GuardrailChecker) -> None:
    result = checker.check("REVOKE SELECT ON foo FROM user")
    assert result.allowed is False


# ---------------------------------------------------------------------------
# SET GLOBAL — blocked
# ---------------------------------------------------------------------------


def test_set_global_blocked(checker: GuardrailChecker) -> None:
    result = checker.check("SET GLOBAL max_connections = 100")
    assert result.allowed is False


# ---------------------------------------------------------------------------
# Multi-statement — blocked
# ---------------------------------------------------------------------------


def test_multi_statement_blocked(checker: GuardrailChecker) -> None:
    result = checker.check("SELECT 1; DROP TABLE foo")
    assert result.allowed is False


def test_semicolon_chaining_blocked(checker: GuardrailChecker) -> None:
    # Two otherwise-safe statements chained — still rejected (not in catalog)
    result = checker.check("SELECT 1; SELECT 2")
    assert result.allowed is False


# ---------------------------------------------------------------------------
# Not-in-catalog SELECTs — blocked regardless of statement type
# ---------------------------------------------------------------------------


def test_lowercase_not_in_catalog_blocked(checker: GuardrailChecker) -> None:
    result = checker.check("select * from pg_stat_activity")
    assert result.allowed is False


def test_arbitrary_select_blocked(checker: GuardrailChecker) -> None:
    result = checker.check("SELECT * FROM users")
    assert result.allowed is False


# ---------------------------------------------------------------------------
# Mixed-case bypass — blocked (not in catalog)
# ---------------------------------------------------------------------------


def test_mixed_case_bypass_blocked(checker: GuardrailChecker) -> None:
    result = checker.check("SeLeCt * FrOm pg_stat_activity")
    assert result.allowed is False


# ---------------------------------------------------------------------------
# Comment bypass — blocked
# ---------------------------------------------------------------------------


def test_inline_comment_bypass_blocked(checker: GuardrailChecker) -> None:
    # Appending a comment to a catalog query must be rejected (not exact match)
    first_catalog_sql = next(iter(DIAGNOSTIC_CATALOG.values()))
    result = checker.check(first_catalog_sql + " -- comment")
    assert result.allowed is False


def test_block_comment_prefix_blocked(checker: GuardrailChecker) -> None:
    result = checker.check("/* comment */ SELECT 1")
    assert result.allowed is False


# ---------------------------------------------------------------------------
# CTE with DML — blocked
# ---------------------------------------------------------------------------


def test_cte_with_dml_blocked(checker: GuardrailChecker) -> None:
    result = checker.check("WITH cte AS (SELECT 1) DELETE FROM foo")
    assert result.allowed is False


# ---------------------------------------------------------------------------
# Stored procedure call — blocked
# ---------------------------------------------------------------------------


def test_call_stored_proc_blocked(checker: GuardrailChecker) -> None:
    result = checker.check("CALL some_proc()")
    assert result.allowed is False


# ---------------------------------------------------------------------------
# GuardrailResult shape
# ---------------------------------------------------------------------------


def test_blocked_result_has_reason(checker: GuardrailChecker) -> None:
    result = checker.check("DROP TABLE foo")
    assert isinstance(result, GuardrailResult)
    assert result.allowed is False
    assert result.reason
    assert result.blocked_pattern


def test_allowed_result_shape(checker: GuardrailChecker) -> None:
    sql = next(iter(DIAGNOSTIC_CATALOG.values()))
    result = checker.check(sql)
    assert isinstance(result, GuardrailResult)
    assert result.allowed is True
    assert result.reason == ""
    assert result.blocked_pattern is None
