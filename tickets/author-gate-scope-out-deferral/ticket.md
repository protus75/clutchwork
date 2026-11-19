---
priority: P1
kind: feature
agent_tier: medium
agent_effort: medium
source: box:suggestion
state: draft
---

## Depends on
none

## Context
- clutch/author.py::slice_follow_up
- clutch/author.py::AuthorGate.check
- tests/unit/test_author_slice_follow_up.py
- clutch/docs/host-authoring.md#What each section is for

## Goal / Why
The Author gate refuses a roadmap-row draft whose Scope out defers row work to "separate tickets" or a "follow-up" that does not exist, so a merge cannot strike the row and drop that work. Today `slice_follow_up` fires only when the Goal contains the word `slice` and never reads Scope out. `serve-parallel-dispatch-r2` (row 45) said "The running-transition writer, the merge-queue run context, the host-command lock and the shared eligible() filter are separate tickets and are out of scope" with no such tickets and `docs/roadmap.md` unfenced; merging it would have struck row 45 and dropped four parts until a supervising session added follow-up rows by hand. The word-`slice` check was the same surface patched once for one keyword, so this generalizes it to the deferral class.

## Boundary contract
### Author gate roadmap-row check
- disposition: extend
- owner: clutch/author.py (`AuthorGate.check` and the `slice_follow_up` helper beside it)
- consumers: the Author stage's `AuthorGate`, for roadmap-row requests only
- observable change: a roadmap-row draft whose `Scope in / Scope out` text matches a deferral phrase (`separate ticket(s)`, `follow-up ticket(s)`, `follow-up row(s)`, `later ticket(s)`, `future ticket(s)`, `another ticket`, `other tickets`), whose fence omits `docs/roadmap.md`, and which names no existing ticket stem in backticks, gets one finding whose paved road says to name an existing ticket stem in backticks, or fence `docs/roadmap.md` and add a follow-up row, or deliver the whole row
- compatibility: the existing `slice` check and its tests are unchanged; non-roadmap requests are never checked; drafts without deferral phrases are unaffected
- acceptance: criteria 1-4 below
- tests: new `tests/unit/test_author_scope_out_deferral.py`
- post-merge source of truth: clutch/author.py

## Scope in / Scope out
In: add a pure helper `deferral_follow_up(roadmap_row, scope_text, fence, repo)` in `clutch/author.py` next to `slice_follow_up`, returning one `Finding` (code `AuthorGate.code`) as described in the boundary contract. A named stem counts only when written in backticks and `repo/tickets/<stem>/ticket.md` exists. The roadmap path comes from `clutch.roadmap.ROADMAP` through a function-level import, as `slice_follow_up` does. Call it from the roadmap-row branch of `AuthorGate.check` with `parsed.sections["Scope in / Scope out"]`, `parsed.scope_fence` and `self.checkout.repo`, guarded as the slice call is. Add one sentence to the `Scope in / Scope out` bullet of `clutch/docs/host-authoring.md` stating that work deferred to separate tickets needs an existing ticket stem or a fenced follow-up roadmap row.
Out: `clutch/specs/requisition_review.md` (a prompt-spec rule needs a version bump and a fenced test pin; file it separately if wanted), `slice_follow_up` and its tests, lint, roadmap parsing, non-roadmap requests.

## Scope fence
- clutch/author.py
- clutch/docs/host-authoring.md
- tests/unit/test_author_scope_out_deferral.py

## Acceptance criteria
1. `./dev.py test tests/unit/test_author_scope_out_deferral.py` shows `deferral_follow_up` returns one finding for Scope out "The writer and the lock are separate tickets and out of scope." with a fence lacking `docs/roadmap.md` and no existing stem, not `[]`, and the finding's paved road names `docs/roadmap.md`.
2. The same test shows the same text returns `[]`, not a finding, when the fence lists `docs/roadmap.md`, and returns `[]` when the text names a backticked stem whose `tickets/<stem>/ticket.md` exists under `tmp_path`; a backticked stem with no such file still returns one finding.
3. The same test shows Scope out without a deferral phrase (for example "Out: lint and roadmap parsing.") returns `[]`, and `roadmap_row=None` returns `[]` for deferral text.
4. The same test drives `AuthorGate.check` with a stubbed `validate_ticket` and shows a roadmap-row reply with deferral Scope out and no roadmap fence gets verdict `fail`, and verdict `pass` once the fence adds `docs/roadmap.md`.
5. `./dev.py test tests/unit/test_author_slice_follow_up.py tests/unit/test_author.py tests/unit/test_author_roadmap_row.py tests/unit/test_lint_guide_parity.py tests/integration/test_lint_guide_parity.py` exits 0.

## Verification
```
./dev.py test tests/unit/test_author_scope_out_deferral.py tests/unit/test_author_slice_follow_up.py tests/unit/test_author.py tests/unit/test_author_roadmap_row.py tests/unit/test_lint_guide_parity.py tests/integration/test_lint_guide_parity.py
```

## Definition of rejected
A roadmap-row draft that defers row work to "separate tickets" with no existing stem and no fenced `docs/roadmap.md` passes the gate, or a non-roadmap request is refused by the new check.

## Time budget
- expected: 15m
- stuck: 30m
