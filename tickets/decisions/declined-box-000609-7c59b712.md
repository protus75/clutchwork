---
id: declined-box-000609-7c59b712
kind: declined
link: box-000609-7c59b712
reopen_after_days: 14
---
Coverage-floor tickets keep pinning per-module floor values from measurements that go stale. Row 22's test-gate-floors was rejected because three modules measured 0% under the unit check. Its replacement draft, test-gate-floors-measured, still pins clutch/thresh.py at 0 with an 'integration-only' comment, even though evidence-envelope has since raised thresh's unit coverage to about 67%. The message asks for a host-authoring.md rule: a floor-setting ticket states the rule (measured unit coverage at the base commit minus N) and never lists per-module values, and Implement measures with the unit check's own argv.

Nothing is going wrong at runtime. The problem is a stale value in a draft ticket that has not run yet, plus a proposed authoring-guide rule to prevent it. The admission bar declines prevention and authoring-wording changes unless they are tied to reachable incorrect behavior. The message cites declined-box-000566 as met, but that record's reopen condition was 'a second floor-setting ticket is rejected or parks on unmeasured floors'. test-gate-floors-measured is still an unconfirmed draft: it has not been rejected or parked. It is held only because roadmap-ahead-skips-held-rows treats drafts as open. The stale thresh value is a fix to one draft ticket, which the draft's owner or a supervising session can make before confirming it; it does not need a new engine ticket. It is not a duplicate: no open or merged ticket or registry record adds this authoring rule. Reopen if test-gate-floors-measured, or any later floor-setting ticket, is rejected, premise-fails, or parks because its pinned floor values no longer match the base-commit measurement.

- declined-box-000566-cb8bafcc reopen condition: 'a second floor-setting ticket is rejected or parks on unmeasured floors'
- Open ticket test-gate-floors-measured is an unconfirmed draft (per roadmap-ahead-skips-held-rows), not rejected or parked
- Message reports that thresh's unit coverage rose to 66.81% after evidence-envelope merged, so the draft's thresh=0 pin and its comment are stale before any run
- Proposed repair is an authoring-guide rule in clutch/docs/host-authoring.md, which is prevention, not a fix for an observed runtime failure; compare declined-box-000584 and declined-box-000586

Message: box-000609-7c59b712
