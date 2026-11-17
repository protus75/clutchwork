---
state: draft
source: box:suggestion
priority: P1
kind: feature
agent_tier: medium
agent_effort: medium
---

## Depends on
none

## Context
- clutch/author.py::author
- clutch/author.py::failure_declined
- clutch/stages.py::findings_text
- tests/unit/test_author.py

## Goal / Why
When an Author attempt declines after several driver calls, the `Evidence:` body of the committed decline record lists every distinct gate finding from the attempt, in the order the calls produced them. Today `author()` passes only `findings_text(result.findings)`, and the driver overwrites its tally on each call, so the record keeps only the last call's refusal. For roadmap row 21 the records `tickets/decisions/declined-box-000639-*.md` and `declined-box-000644-*.md` showed only `roadmap row requires stem test-fakes-and-conftest`. The earlier refusal `stem is already named in the journal` was hidden. A supervisor misdiagnosed the row as a one-stem split refusal, and the draft `roadmap-row-split-parts` was rejected on that false cause. The decline record is the artifact the Diagnosis rules send supervisors to read, so it must show the whole attempt.

Cause fix, not an instance fix: the collection point is `render_author` in `clutch/author.py`. The driver calls it with the re-prompt findings of each failed call, so it sees every refusal except the final one, which arrives in `result.findings`.

## Scope in / Scope out
Scope in: in `clutch/author.py::author`, keep an ordered list of findings. `render_author` appends each finding it receives, skipping one already in the list (same `code` and `message`). On the decline at `result.outcome != "ok"`, build the `Evidence:` text with `findings_text` over the collected findings followed by `result.findings`, again skipping duplicates. Order is first-seen. The output keeps the `- code: message (do instead: ...)` line format. When no findings were collected the text is unchanged from today.
Scope out: the other `failure_declined` call sites, the decline record format, driver tally behavior, and `docs/`. No new module, no knob.

## Scope fence
- clutch/author.py
- tests/unit/test_author_decline_findings.py

## Acceptance criteria
1. Two scripted driver calls whose re-prompt findings are `A` (first) then `B` (final, in `result.findings`) make `failure_declined` receive evidence with the `A` line before the `B` line; `tests/unit/test_author_decline_findings.py` asserts both are present, not just `B`.
2. A finding repeated in a later call's findings appears once in the evidence; the test asserts the `A` line count is 1, not 2.
3. A single-call decline with one finding yields exactly `findings_text([finding])`, the same as before the change; `tests/unit/test_author_decline_findings.py` asserts equality with that string.
4. `./dev.py test tests/unit/test_author.py tests/unit/test_author_decline_findings.py tests/integration/test_author.py` passes.

## Verification
```
./dev.py test tests/unit/test_author.py tests/unit/test_author_decline_findings.py tests/integration/test_author.py
```

## Definition of rejected
The evidence still holds only the last call's findings, or it drops the last call's findings, or the change adds a driver, journal or record-format change.

## Time budget
- expected: 15m
- stuck: 30m
