---
id: declined-box-001140-6bf42f1c
kind: declined
link: box-001140-6bf42f1c
reopen_after_days: 30
---
Author could not produce a ticket.

Evidence: - ticket_schema: a `kind: bug` ticket has no evidence file (do instead: add the observed failure (output, log excerpt, or captured command output) as a file under tickets/handoff-execs-engine-python/evidence; the evidence file must not be gitignored)
- ticket_schema: documents named in Scope in are not fenced: docs/how-clutch-works.md (do instead: fence the document and say which part to update, or drop the mention)
- requisition_review: invalid requisition review reply: 1 schema error(s) (do instead: reply with a schema-valid requisition verdict)
- incomplete-scope-in: Scope in names only the prefix-slice comparison (`argv[:9]`) and the full spawned-argv assertion in tests/integration/test_drain_upgrade.py. Two other lines also hard-code the old 7-element `uv run --project <engine> python -m clutch` prefix. `Child.replace` calls `main(list(argv[7:]), ...)` to strip the prefix. `test_the_carried_parked_set_rides_every_handoff_in_the_chain` asserts `[s["argv"][9:] ...]`. With the 3-element prefix, the first passes `-m clutch ...` to main and the second slices at the wrong offset. Both fail, so criterion 3 cannot pass. (do instead: Add to Scope in that `Child.replace` must slice `argv[3:]` instead of `argv[7:]`. Also add that the carried-parked-set test must slice `argv[5:]` instead of `argv[9:]`, and that the comment above the `main` call must be updated. Both lines are in the already-fenced file.)
