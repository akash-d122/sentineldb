"""
Tests for the diagnostic query catalog.
Every catalog entry must be a non-empty string and pass the GuardrailChecker.
"""
import pytest

from sentineldb.guardrails.catalog import DIAGNOSTIC_CATALOG
from sentineldb.guardrails.checker import GuardrailChecker


@pytest.fixture
def checker() -> GuardrailChecker:
    return GuardrailChecker()


def test_catalog_is_nonempty() -> None:
    assert len(DIAGNOSTIC_CATALOG) > 0


def test_catalog_keys_are_strings() -> None:
    for key in DIAGNOSTIC_CATALOG:
        assert isinstance(key, str) and key.strip(), f"Bad catalog key: {key!r}"


def test_catalog_values_are_nonempty_strings() -> None:
    for name, sql in DIAGNOSTIC_CATALOG.items():
        assert isinstance(sql, str) and sql.strip(), f"Catalog entry '{name}' has empty SQL"


def test_all_catalog_queries_allowed_by_checker(checker: GuardrailChecker) -> None:
    for name, sql in DIAGNOSTIC_CATALOG.items():
        result = checker.check(sql)
        assert result.allowed is True, (
            f"Catalog entry '{name}' is blocked by GuardrailChecker: {result.reason}"
        )


def test_required_catalog_keys_present() -> None:
    required = {
        "active_connections",
        "waiting_connections",
        "replication_lag",
        "db_size",
    }
    missing = required - set(DIAGNOSTIC_CATALOG.keys())
    assert not missing, f"Catalog missing required keys: {missing}"
