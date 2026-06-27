# Slow Query Spike

## Symptoms
- High slow query count via pg_stat_statements.
- CPU pressure from query execution.
- Increased query latency across the database.
- Application response times degrading.

## Evidence To Collect
- Slow query count (pg_stat_statements mean_exec_time > 1000ms).
- CPU utilisation on the database host.
- Active connection count.
- Top query fingerprints by mean execution time.
- Recent schema or index changes.

## Safe Checks
- Run EXPLAIN on the flagged slow query fingerprint.
- Check pg_stat_statements for top mean_exec_time queries.
- Review pg_stat_database for sequential scan spikes.
- Check for recent deploy or data volume change.

## Requires DBE Approval
- Adding or modifying indexes.
- Killing long-running queries (pg_terminate_backend).
- Query plan hint injection.
- Schema changes to improve performance.
