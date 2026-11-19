---
id: tombstone-box-000787-1e49ffe0
kind: tombstone
link: declined-box-000443-db18b23e
reopen_after_days: 14
---
Codex at the Implement stage keeps giving up on large tickets. After about 50-90 s and a partial edit it replies `incomplete`, without hitting its budget or any blocker. On 2026-11-19 this burned seven attempts across serve-parallel-dispatch-r1, merge-model-resolve and conflict-discard-rerun before Diagnose split the work. The note proposes two fixes: a keep-working instruction in implement.md, and authoring-time flagging of tickets too large for one Implement call, based on how often past `incomplete` outcomes matched fence size.

The registry has already decided this. Record 000443 declined the same problem: codex quits Implement with `incomplete` on large tickets, and the note proposed a size warning or ceiling when a ticket is authored or rendered, which is what this note's second fix asks for. Record 000604 already tombstoned a restatement to 000443. The first fix already exists. clutch/specs/implement.md line 88, added by the merged implement-spec-no-quit-after-reading, says that stopping after only reading, or because the change is large, is never a reason for `incomplete`, and to keep editing. This note adds new stems but no new failure mechanism and no new repair. Reopen in 14 days if the spool outputs show codex giving up despite that line in a way the existing spec text cannot fix, for example a provider-side turn limit, and the evidence names one bounded engine change.

- declined-box-000443-db18b23e: codex quit Implement with `incomplete` on large prompts (7 of 15 at 80 KB or more); proposed fixes were a render ceiling, a size warning at authoring, or a higher tier
- tombstone-box-000604-57447cda: codex fast `incomplete` on wide tickets, linked to 000443
- clutch/specs/implement.md:88 already says stopping because the change is large is never a reason for `incomplete`; keep editing
- merged stems implement-incomplete-outcome and implement-spec-no-quit-after-reading
- .clutch/state/spools/conflict-discard-rerun/{0,1,2}/implement/call-01/output.txt exist

Message: box-000787-1e49ffe0
