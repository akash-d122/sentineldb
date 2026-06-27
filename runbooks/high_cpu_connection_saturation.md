# High CPU - Connection Saturation

## Symptoms
- DB CPU above threshold.
- Active connections above 80% of max connections.
- Waiting sessions increasing.
- Slow query count may increase due to queuing.

## Evidence To Collect
- Current CPU metric.
- Active connections and max connections.
- Waiting sessions.
- Top query fingerprints.
- Replication lag.
- Disk/read/write latency.

## Safe Checks
- Check active sessions using approved diagnostic query.
- Check top query fingerprints.
- Run EXPLAIN on flagged read query if available.
- Check recent application deploy or traffic spike.

## Requires DBE Approval
- Killing sessions.
- Restarting DB/application services.
- Changing connection pool settings.
- Adding indexes.
