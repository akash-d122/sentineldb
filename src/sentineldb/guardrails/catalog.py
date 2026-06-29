"""
Approved diagnostic query catalog — the allowlist for GuardrailChecker.

Only queries listed here may be executed against monitored databases.
Each entry maps a stable name to an exact SQL template.
The checker performs an exact-string match (stripped, normalised whitespace).
"""

DIAGNOSTIC_CATALOG: dict[str, str] = {
    # Active connection count and max_connections
    "active_connections": (
        "SELECT count(*) AS active_connections "
        "FROM pg_stat_activity "
        "WHERE state = 'active'"
    ),
    # Max allowed connections for the instance
    "max_connections": "SHOW max_connections",
    # Waiting connections (lock-blocked)
    "waiting_connections": (
        "SELECT count(*) AS waiting_connections "
        "FROM pg_stat_activity "
        "WHERE wait_event_type IS NOT NULL AND state = 'active'"
    ),
    # Replication lag in seconds (primary side)
    "replication_lag": (
        "SELECT EXTRACT(EPOCH FROM (now() - pg_last_xact_replay_timestamp())) "
        "AS replication_lag_seconds"
    ),
    # Database size in bytes
    "db_size": (
        "SELECT pg_database_size(current_database()) AS db_size_bytes"
    ),
    # Slow query count via pg_stat_statements (requires extension)
    "slow_query_count": (
        "SELECT count(*) AS slow_query_count "
        "FROM pg_stat_statements "
        "WHERE mean_exec_time > 1000"
    ),
    # All databases summary
    "pg_stat_database": (
        "SELECT datname, numbackends, xact_commit, xact_rollback, "
        "blks_read, blks_hit, tup_returned, tup_fetched "
        "FROM pg_stat_database "
        "WHERE datname = current_database()"
    ),
}
