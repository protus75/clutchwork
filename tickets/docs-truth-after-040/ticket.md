---
state: confirmed
priority: P1
kind: chore
agent_tier: medium
agent_effort: medium
source: human
---

## Depends on
- none

## Context
- docs/boundary-contract-plan.md
- docs/parallel-tickets-plan.md
- docs/gemini-graphics-refactor-plan.md
- docs/how-clutch-works.md
- clutch/tickets.py::REQUIRED_SECTIONS
- clutch/tickets.py::_boundary_findings
- clutch/docs/host-authoring.md
- tickets/boundary-contract-required/ticket.md
- tickets/conflict-rerun-runs-alone/ticket.md

## Goal / Why
Roadmap row 163. Four documents still describe the state before the 0.4.0 merges, so a reader (or an agent that loads them as context) is told work is planned that has merged, and is not told what is still open.

1. `docs/how-clutch-works.md` section 3.1 lists the frontmatter fields and never mentions the `## Boundary contract` section, although `clutch/tickets.py::REQUIRED_SECTIONS` now requires it for every non-settled ticket and `boundary-contract-plan.md`'s "Where the eventual rules belong" table makes that file the home of current behavior.
2. `docs/boundary-contract-plan.md` Status says "Requiring the section ... remain[s] pending"; `boundary-contract-required` (row 154) merged it.
3. `docs/parallel-tickets-plan.md` Status says parallel dispatch, conflict resolution and the hot-paths view "remain planned (rows 42-48)"; rows 42-48 merged (`parallel-config`, `fence-overlap`, `chain-order`, `serve-parallel-dispatch-r2`, `merge-model-resolve`, `conflict-discard-rerun-r1`, `status-hot-paths`), as did the follow-ups `serve-parallel-fill-slots` (row 164).
4. `docs/gemini-graphics-refactor-plan.md` Status says "The graphics ticket kind and visual review remain planned (rows 49-55)"; rows 49-55 merged, as did `graphics-select-waits-go` (row 169).

After this change each Status section names what merged and what remains, and section 3.1 names the required section and points at the guide that owns its content.

## Boundary contract
none
- reason: documentation-only change; it adds no code boundary and edits no owner, consumer or format. Each document's description changes to match behavior that `clutch/tickets.py` and the merged tickets already own.

## Scope in / Scope out
Scope in. Read each claim against the code at HEAD before writing it; do not copy this ticket's lists into the documents unchecked.

- `docs/how-clutch-works.md` section 3.1: add one bullet to the "Frontmatter fields that drive behavior" area, or a sentence directly after it, saying a non-settled ticket must carry a `## Boundary contract` section, that a ticket whose state is `merged` or `rejected` is exempt, that intake and `clutch ticket lint` check the section's presence and basic shape, and that [the authoring guide](../clutch/docs/host-authoring.md) owns its fields, dispositions and `none` reasons. Describe only what `clutch/tickets.py::lint` and `_boundary_findings` do now; add no heading.
- `docs/boundary-contract-plan.md` Status (only the Status paragraph): say the authoring rollout and the requirement merged (rows 150, 151, 154) and what remains: `boundary-contract-lint` (row 152, provisional, promoted only on evidence from deployed reviews) and `boundary-contract-implementation-review` (row 153, authored, not merged). Keep the existing sentence on the trial.
- `docs/parallel-tickets-plan.md` Status (only the Status paragraph): name rows 42-48 as merged and `serve-parallel-fill-slots` (row 164) as merged, and name what remains from the roadmap's open parallel rows: `conflict-rerun-runs-alone` (row 165, authored, not merged), `serve-dispatch-returns-on-slot` (row 166), `retro-conflict-path-proposals` (row 167) and `parallel-gate-merge-count` (row 168). Read the roadmap document's section 8 for each row's current text and state, and verify against code that `clutch/scheduler.py::Scheduler.dispatch_next` and `clutch/retro.py` still lack what rows 166 and 167 describe; if a row has merged since this ticket was written, name it as merged instead.
- `docs/gemini-graphics-refactor-plan.md` Status (only the Status paragraph): name rows 49-55 and 169 as merged and say what remains: a recorded `visual_baseline` GO (until then every graphics ticket parks at B6). Read `clutch/policy.py` and the roadmap document's decision 17 for the exact wording.

Scope out: the "Current state", "Roadmap", "Departures" and every other section of the three plans; the roadmap document (the driver strikes rows); the frozen bootstrap plan; any code, spec or test; no new test or standing check that pins document wording; any other stale claim noticed in these documents (file it with `clutch suggest`).

## Scope fence
- docs/how-clutch-works.md
- docs/boundary-contract-plan.md
- docs/parallel-tickets-plan.md
- docs/gemini-graphics-refactor-plan.md

## Acceptance criteria
1. `docs/how-clutch-works.md` section 3.1 contains the text `## Boundary contract`, the word `exempt` or `settled`, and a link to `host-authoring.md`; checked by the python assertion in `## Verification` against the text between the `### 3.1 ` and `### 3.2 ` headings. Ruled out: the name appearing only elsewhere in the file.
2. `docs/boundary-contract-plan.md`'s Status no longer contains `Requiring the section` followed by `pending`, and names `boundary-contract-required` or row 154, `boundary-contract-lint` and `boundary-contract-implementation-review`; checked by the python assertion in `## Verification`.
3. `docs/parallel-tickets-plan.md`'s Status no longer contains `remain planned (rows 42`, and names `serve-parallel-fill-slots`, `conflict-rerun-runs-alone`, `serve-dispatch-returns-on-slot` and `retro-conflict-path-proposals`; checked by the python assertion in `## Verification`.
4. `docs/gemini-graphics-refactor-plan.md`'s Status no longer contains `remain planned (rows 49`, and names `graphics-select-waits-go` and `visual_baseline`; checked by the python assertion in `## Verification`.
5. Only the four fenced documents changed: `git diff --name-only main` lists no other path. Each plan's diff touches only its Status paragraph.
6. `./dev.py test` exits 0, so no test that reads these documents (help links, roadmap table, parity) broke.

## Verification
```
uv run python -I -c "import pathlib,re; h=pathlib.Path('docs/how-clutch-works.md').read_text(); s=h.split('### 3.1 ')[1].split('### 3.2 ')[0]; assert '## Boundary contract' in s and 'host-authoring.md' in s and ('exempt' in s or 'settled' in s); st=lambda p: pathlib.Path(p).read_text().split('## Status')[1].split('\n## ')[0]; b=st('docs/boundary-contract-plan.md'); assert 'boundary-contract-lint' in b and 'boundary-contract-implementation-review' in b and ('154' in b or 'boundary-contract-required' in b); p=st('docs/parallel-tickets-plan.md'); assert 'remain planned (rows 42' not in p and all(x in p for x in ('serve-parallel-fill-slots','conflict-rerun-runs-alone','serve-dispatch-returns-on-slot','retro-conflict-path-proposals')); g=st('docs/gemini-graphics-refactor-plan.md'); assert 'remain planned (rows 49' not in g and 'graphics-select-waits-go' in g and 'visual_baseline' in g"
./dev.py test
```

## Definition of rejected
The branch is rejected if it edits any file outside the fence, edits a section of a plan other than its Status paragraph (plus the one section 3.1 addition), adds a test or lint that pins document wording, states a merged or remaining fact it did not check against the roadmap and the code, or copies rule text from `clutch/docs/host-authoring.md` into `docs/how-clutch-works.md` instead of linking it.

## Time budget
- expected: 25m
- stuck: 50m
