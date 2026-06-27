# DB Unreachable

## Symptoms
- TCP connection or DB login fails.
- Application cannot connect.
- Health check reports DB down.

## Evidence To Collect
- Connection error type.
- RDS/EC2 status checks if available.
- DNS/endpoint string.
- Recent credential/config changes if known.

## Safe Checks
- Validate instance registry entry.
- Check whether error is timeout, authentication failure, or connection refused.
- Check cloud status metric if available.

## Requires DBE Approval
- Restarting DB service.
- Failover.
- Security group/firewall changes.
- Credential rotation.
