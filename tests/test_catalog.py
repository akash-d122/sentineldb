"""
Tests for the diagnostic query catalog.
Every catalog entry must be a non-empty string and pass the GuardrailChecker.
"""

import pytest

from sentineldb.guardrails.catalog import MYSQL_CATALOG, POSTGRES_CATALOG
from sentineldb.guardrails.checker import GuardrailChecker


@pytest.fixture
def checker() -> GuardrailChecker:
    return GuardrailChecker()


def test_catalogs_are_nonempty() -> None:
    assert len(POSTGRES_CATALOG) > 0
    assert len(MYSQL_CATALOG) > 0


def test_catalog_keys_are_strings() -> None:
    for key in POSTGRES_CATALOG:
        assert isinstance(key, str) and key.strip(), f"Bad Postgres catalog key: {key!r}"
    for key in MYSQL_CATALOG:
        assert isinstance(key, str) and key.strip(), f"Bad MySQL catalog key: {key!r}"


def test_catalog_values_are_nonempty_strings() -> None:
    for name, sql in POSTGRES_CATALOG.items():
        assert isinstance(sql, str) and sql.strip(), (
            f"Postgres Catalog entry '{name}' has empty SQL"
        )
    for name, sql in MYSQL_CATALOG.items():
        assert isinstance(sql, str) and sql.strip(), f"MySQL Catalog entry '{name}' has empty SQL"


def test_all_catalog_queries_allowed_by_checker(checker: GuardrailChecker) -> None:
    for name, sql in POSTGRES_CATALOG.items():
        result = checker.check(sql, engine="postgresql")
        assert result.allowed is True, (
            f"Postgres Catalog entry '{name}' is blocked by GuardrailChecker: {result.reason}"
        )
    for name, sql in MYSQL_CATALOG.items():
        result = checker.check(sql, engine="mysql")
        assert result.allowed is True, (
            f"MySQL Catalog entry '{name}' is blocked by GuardrailChecker: {result.reason}"
        )


def test_required_catalog_keys_present() -> None:
    required = {
        "active_connections",
        "waiting_connections",
        "replication_lag",
        "db_size",
        "lock_contention",
        "long_running_transactions",
    }
    missing_pg = required - set(POSTGRES_CATALOG.keys())
    assert not missing_pg, f"Postgres Catalog missing required keys: {missing_pg}"

    missing_mysql = required - set(MYSQL_CATALOG.keys())
    assert not missing_mysql, f"MySQL Catalog missing required keys: {missing_mysql}"
