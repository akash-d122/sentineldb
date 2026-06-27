# Replication Lag

## Symptoms
- Replica lag above threshold.
- Read replicas return stale data.
- Replication delay persists for more than configured window.

## Evidence To Collect
- Current lag seconds.
- Primary write volume.
- Replica CPU and IO pressure.
- Replication status.
- Long-running transactions.

## Safe Checks
- Check replication status using approved diagnostic query.
- Check long-running transactions.
- Compare lag with historical baseline.

## Requires DBE Approval
- Replica restart.
- Failover.
- Topology changes.
- Config changes.
