# Runbook: Payment Service Outage (P1)

**Service**: payments
**Severity**: P1
**Owner**: platform-team
**Last updated**: 2025-11-02

## Symptoms
- `payments-api` 5xx rate spikes; checkout failures reported by support.
- Dashboard: `payments-overview` shows request success rate < 99%.

## Diagnosis
1. Check recent deploys: `kubectl -n payments rollout history deployment/payments-v1`
2. Check pod status: `kubectl -n payments get pods -l app=payments-v1`
3. Check upstream DB health (see `db-failover.md` if DB is the cause).

## Mitigation
1. If a bad deploy is suspected, roll back:
   `kubectl -n payments rollout undo deployment/payments-v1`
2. If load-related, scale out to the standard capacity of **3 replicas**:
   `kubectl -n payments scale deployment/payments-v1 --replicas=3`
3. Restart as a last resort:
   `kubectl -n payments rollout restart deployment/payments-v1`

## Rollback / Verification
- Verify success rate returns > 99.9% on `payments-overview` for 15 minutes.
- If rollback made things worse, re-apply the previous manifest from git tag.

## Escalation
- Page `oncall-platform` if not mitigated within 30 minutes.
