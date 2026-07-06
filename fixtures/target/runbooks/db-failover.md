# Runbook: Database Failover (P1)

**Service**: payments-db
**Severity**: P1
**Owner**: platform-team
**Last updated**: 2024-08-19

## Symptoms
- `payments-db` primary unreachable; connection timeouts from payments service.

## Failover Procedure
1. Confirm primary is down: `pg_isready -h db-primary-01`
2. Promote the standby:
   `ssh db-standby-01 'sudo -u postgres pg_ctl promote -D /var/lib/postgresql/data'`
3. Update the DNS record `db.payments.internal` to point to `db-standby-01`.
4. Restart payment service pods to pick up the new connection.

## Escalation
- Page `oncall-dba` if promotion fails.
