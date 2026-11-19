---
id: tombstone-box-000799-92a770af
kind: tombstone
link: harvest-usd-source-flags
reopen_after_days: 30
---
On conflict-discard-rerun, Diagnose saw the harvest's usd figure of exactly 1.0 and concluded that a spend cap or per-attempt budget had stopped the run. That figure is only the flat est_cost_per_call_usd estimate: codex reports no cost, and no budget was passed to it. Diagnose also stated the wrong provider for attempt 0. The false cause sent a buildable stem to the Reject queue and drove a needless split. The finding asks the Diagnose spec to forbid naming a budget stop from a cost figure alone and to state provider and model only as the record gives them.

The open ticket harvest-usd-source-flags already covers this. It makes harvest.json say whether usd was reported by the provider or is the flat est_cost_per_call_usd estimate, whether the provider can enforce a budget cap, and which provider and model ran the attempt. It also makes the Diagnose spec forbid a budget-stop lesson unless the record shows a reported cost. Together these fix the invented spend-cap cause and the wrong provider claim this finding describes. Reopen if harvest-usd-source-flags merges and Diagnose still names a budget or spend-cap stop based only on an estimated cost figure.

- Open ticket harvest-usd-source-flags: harvest.json says whether usd was provider-reported or the flat limits.est_cost_per_call_usd, whether the provider can enforce a budget cap, and which provider and model ran the attempt; the Diagnose spec forbids a budget-stop lesson unless the record shows a reported cost.
- Message: in conflict-discard-rerun, the attempt 1 diagnosis read usd=1.0 as a shared spend cap and chose abandon-human; the attempt 2 diagnosis chose split, citing per-attempt budget; the operator's kill verdict said codex reports no cost and usd=1.0 is the flat config estimate.
- The proposed repair path, clutch/specs/diagnose.md, is the same Diagnose spec surface the open ticket changes.

Message: box-000799-92a770af
