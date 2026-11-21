---
state: rejected
source: box:roadmap_row
priority: P1
kind: chore
agent_tier: medium
agent_effort: medium
---

## Depends on
none

## Context
- clutch/roadmap.py::merged
- clutch/tickets.py::parse_ticket
- tests/unit/test_roadmap_merged.py

## Goal / Why
Roadmap row 173 `graphics-generate-first-ticket`. The 0.4.0 ship clause wants one `mode: generate` graphics ticket merged through the `clutch(<stem>): select` commit that `clutch/stages.py` writes. The 0.4.0 gate block has no command that checks it, so the release can pass without it (see the paragraph under the 0.4.0 table in `docs/roadmap.md`). When this ticket is done, `clutch roadmap merged --graphics-select` exits 0 only when some ticket reachable from HEAD has `kind: graphics`, a `## Render` section with `- mode: generate`, and a commit whose subject is `clutch(<stem>): select`; otherwise it exits non-zero and names the missing condition. The 0.4.0 gate block runs it. The gate then fails until the first generate ticket merges, which is the point.

Authoring and running that graphics ticket is a separate step: Implement cannot write `tickets/` files, and a ticket cannot run itself. This ticket adds the gate check and a follow-up roadmap row for that step.

## Boundary contract
### roadmap merged verb
- disposition: extend
- owner: clutch/roadmap.py::merged
- consumers: the 0.4.0 gate block in docs/roadmap.md, `clutch roadmap status`, and operators of `clutch roadmap merged`
- observable change: new flag `--graphics-select` on `clutch roadmap merged`. It adds a finding line `roadmap merged: no merged generate graphics ticket has a select commit` when no stem qualifies, and adds nothing otherwise. A qualifying stem needs a commit subject `clutch(<stem>): select` in HEAD history and, in `tickets/<stem>/ticket.md` at HEAD, `kind: graphics` with `- mode: generate` under `## Render`. It combines with the other conditions as an extra finding source, so the existing all-conditions-pass rule is unchanged. Alone it satisfies the existing `no condition` refusal.
- compatibility: every existing flag and finding line is unchanged; the flag defaults off and callers that do not pass it behave as before.
- acceptance: a fake history with a generate graphics ticket and its select commit passes; a command-mode graphics ticket, a non-graphics ticket with a select-style subject, and a generate ticket with no select commit each fail.
- tests: new unit tests in tests/unit/test_roadmap_merged_graphics.py
- post-merge source of truth: clutch/roadmap.py::merged

## Scope in / Scope out
Scope in:
- `clutch/roadmap.py::merged`: add keyword `graphics_select=False` and the check. Read git history through `checkout.git` as the existing `--since` branch does (do not use `--first-parent` for the subject scan if the select commit lives on the ticket branch; read `clutch/merge.py` to confirm how branch commits reach main). Read ticket kind and render mode with the parser owned by `clutch/tickets.py`; do not re-parse frontmatter by hand.
- `clutch/__main__.py`: add the `--graphics-select` flag on the `roadmap merged` parser, pass it through at the call site, and add it to that command's description and examples (command-help rule).
- `tests/unit/test_roadmap_merged.py`: the one existing expectation that changes is the exact kwargs dict at the CLI pass-through assertion, which gains `"graphics_select": False`.
- `docs/how-clutch-works.md` section 2 verb table and `clutch/docs/host-running.md` verb row for `roadmap merged`: mention the flag.
- `docs/roadmap.md`: add the command `uv run clutch roadmap merged --graphics-select` to the 0.4.0 gate block; update the paragraph under the 0.4.0 table so it no longer says the graphics ship clause is unchecked (the `visual_baseline` GO clause stays unchecked, row 174); add one new 0.4.0 row, next free number, for authoring and running one `mode: generate` graphics ticket, kind chore, P1, with Depends on this row's stem. Do not add a test pinning roadmap text; verification is that the roadmap parses.
Scope out:
- Authoring or running the generate graphics ticket itself: the new roadmap row above.
- The `visual_baseline` GO gate: `visual-baseline-go-gate` (row 174).
- `clutch/stages.py`, `clutch/git.py`, `clutch/help.py`, extension code.

## Scope fence
- clutch/roadmap.py
- clutch/__main__.py
- tests/unit/test_roadmap_merged.py
- tests/unit/test_roadmap_merged_graphics.py
- docs/how-clutch-works.md
- clutch/docs/host-running.md
- docs/roadmap.md

## Acceptance criteria
1. With a fake history holding `clutch(art): select` and `tickets/art/ticket.md` of `kind: graphics` with `- mode: generate`, `roadmap.merged(..., graphics_select=True)` returns `(True, ["roadmap merged: ok"])`, not a failure; checked by `./dev.py test tests/unit/test_roadmap_merged_graphics.py`.
2. With the same history but `- mode: command`, the result is `(False, ["roadmap merged: no merged generate graphics ticket has a select commit"])`, not a pass; checked by `./dev.py test tests/unit/test_roadmap_merged_graphics.py`.
3. With a generate graphics ticket and no select commit, and with a select-subject commit for a `kind: feature` ticket, each returns the same failure line, not a pass; checked by `./dev.py test tests/unit/test_roadmap_merged_graphics.py`.
4. `graphics_select=True` alone does not raise the `no condition` refusal, and omitting it leaves every existing result unchanged; checked by `./dev.py test tests/unit/test_roadmap_merged.py tests/unit/test_roadmap_merged_graphics.py`.
5. `clutch roadmap merged --graphics-select` parses and passes `graphics_select=True` through, and the command help text names the flag; checked by `./dev.py test tests/unit/test_roadmap_merged.py tests/unit/test_main_help.py`.
6. `docs/roadmap.md` still parses and its 0.4.0 gate block contains the new command; checked by `./dev.py test tests/unit/test_roadmap_gate.py tests/unit/test_roadmap_table.py`.

## Verification
```
./dev.py test tests/unit/test_roadmap_merged.py tests/unit/test_roadmap_merged_graphics.py tests/unit/test_roadmap_gate.py tests/unit/test_roadmap_table.py tests/unit/test_main_help.py
```

## Definition of rejected
The flag passes on a command-mode graphics ticket or on a select-subject commit of a non-graphics ticket; or existing `roadmap merged` behavior changes without the flag; or a test pins roadmap prose.

## Time budget
- expected: 20m
- stuck: 40m
