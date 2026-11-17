---
state: confirmed
priority: P1
kind: chore
agent_tier: medium
agent_effort: medium
source: box:suggestion
---

## Depends on
none

## Context
- clutch/author.py::author
- clutch/author.py::AuthorGate.check
- clutch/author.py::failure_declined

## Goal / Why
Author never overwrites a ticket file that appeared after the gate checked the stem. `AuthorGate.check` refuses an existing `tickets/<stem>/ticket.md` only while it judges the candidate. The review model call that follows can take minutes. `author()` then writes and commits the path without looking again. A human who ran `clutch ticket new <stem>` in that window (untracked skeleton, `source: human`) had it silently replaced by a `box:roadmap_row` draft. After this ticket, `author()` checks the path again immediately before the write. If a file now exists that the gate did not copy in itself, it declines through `failure_declined`, leaves the file bytes unchanged, and makes no commit.

## Scope in / Scope out
In: in `clutch/author.py::author`, just before the `checkout.fs.write` call, apply the same condition `AuthorGate.check` uses: the path exists and `reply.stem` is not in `author_gate.copied`. When it holds, call `author_gate.cleanup()` and return `failure_declined` with evidence naming the stem as claimed since the gate check. Nothing else in `author()` changes.
In: `tests/unit/test_author_roadmap_row.py` has one test that calls `author.author()` twice with stem `sample-row` (around lines 193-199), with a fake commit and `AuthorGate.check` patched to pass, so the first call leaves `tickets/sample-row/ticket.md` on disk. The new re-check would make the second call decline. Add a line that deletes `tickets/sample-row/ticket.md` between those two calls, so the second call still exercises the normal written-and-committed path. That deletion is the only change to that file.
Out: intake behavior, the gate's own check, spec text, docs, and any other stem-claim mechanism.

## Scope fence
- clutch/author.py
- tests/unit/test_author_stem_claimed.py
- tests/unit/test_author_roadmap_row.py

## Acceptance criteria
1. A test creates `tickets/<stem>/ticket.md` with known bytes after the gate check passes and before the write, then runs `author()`. `./dev.py test tests/unit/test_author_stem_claimed.py` asserts the file bytes are unchanged, not replaced by the reply text.
2. The same test asserts `checkout.git.commit` was never called for that stem, not called once.
3. The same test asserts the outcome is a decline (the `failure_declined` result), not a success outcome.
4. A second test in that file runs `author()` with no pre-existing file and asserts the ticket is written and committed, so the new check does not refuse the normal path. `./dev.py test tests/unit/test_author_stem_claimed.py` covers it.
5. `./dev.py test tests/unit/test_author.py tests/unit/test_author_roadmap_row.py` exits 0, so existing flows, including a stem copied in by the gate and the two-call roadmap row test, still succeed.

## Verification
```
./dev.py test tests/unit/test_author_stem_claimed.py tests/unit/test_author.py tests/unit/test_author_roadmap_row.py
```

## Definition of rejected
The branch is rejected if any path still overwrites an existing non-gate-copied ticket file, if the check is placed before the review call instead of just before the write, or if the test uses only a file that existed before the gate check.

## Time budget
- expected: 20m
- stuck: 40m
