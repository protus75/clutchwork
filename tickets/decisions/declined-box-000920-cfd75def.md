---
id: declined-box-000920-cfd75def
kind: declined
link: box-000920-cfd75def
reopen_after_days: 30
---
When a ticket bumps a prompt spec, the authoring guide and lint require it to fence a test that pins the spec's version. Those pins are hardcoded literals in two files: the (name, version) parameter list in tests/integration/test_specs_delimiter_note.py and the version literals in tests/unit/test_specs.py. So every spec-bumping ticket fences the same two files, and the parallel scheduler runs them one at a time. On 2026-11-21 the scheduler skipped dispatching implement-spec-meta-headers-from-verbs while diagnose-spec-engine-written-failure-abandons was running. The proposal is to make these tests read the live version, or check only that the version is a valid major.minor, and to drop the pin requirement from clutch/docs/host-authoring.md and from lint.

Nothing here is incorrect runtime behavior. The scheduler is doing what it should: two tickets that fence the same file run one after the other. The pins are there on purpose. The authoring guide (host-authoring.md lines 110-112) and lint require a fenced test pin so that every spec bump is a deliberate, reviewed change. What the message reports is lost throughput: one dispatch_skip, plus a possible textual merge conflict between adjacent tuples. It cites no failed run, no lost attempt, and no merge conflict that actually happened. The fix it proposes changes tests and an authoring rule, and the admission bar declines that unless it is tied to reachable incorrect behavior. Registry record declined-box-000818-0d328723 already declined a proposal about the same version pins (centralise ownership of the pins), and this message adds only scheduling evidence. Reopen if spec-pin fence overlap causes a merge conflict that costs an attempt or a cap, or if journal data shows spec-bumping tickets repeatedly delayed by spec-pin contention long enough to stall the drain (for example, several hours of idle slots over a window).

- clutch/docs/host-authoring.md:110-112 requires a bumped prompt spec to fence a test pin, and says lint enforces it
- tests/integration/test_specs_delimiter_note.py:16-34 parametrizes literal (name, version) pairs and asserts spec.meta.version == version
- The message cites one dispatch_skip at 2026-11-21 07:47Z. That is fence-overlap serialization, which is the scheduler working as designed, not a failure
- declined-box-000818-0d328723 already declined a proposal about the same version pins forcing test edits on every bump
- The message reports no merge conflict, failed attempt, or spent cap caused by the shared pin files

Message: box-000920-cfd75def
