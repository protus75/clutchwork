---
state: confirmed
source: box:roadmap_row
priority: P1
kind: chore
agent_tier: medium
agent_effort: medium
---

## Depends on
none

## Context
- docs/roadmap-driver-plan.md
- docs/evidence-trail-plan.md#Status

## On-demand
- docs/roadmap.md

## Goal / Why
Roadmap row 124. Merged row 104 did not reach every stale claim, so the roadmap section 1 ship clause (a clean next audit) cannot hold. After this ticket these claims match the code:
- `docs/roadmap-driver-plan.md` Status and section 6 call the idle-point supervisor hook and row 108 planned. `clutch/supervise_idle.py::supervise_idle` already runs from `clutch/serve.py` and `clutch/drain.py`, and the kept release packages have merged (ticket `release-packages-kept`).
- `docs/roadmap-driver-plan.md` section 5 and the "Where each piece lives" row for `publish` name `./dev.py vscode-publish`. Roadmap decision 20 dropped it: the owner publishes the kept package by hand, and `dev.py` has only `vscode-package`.
- `docs/evidence-trail-plan.md` Status says nothing is in effect. Rows 28-31 and 33 have merged, and the `evidence-rusage-capture` ticket is still open.
- `docs/roadmap.md` section 1 prose says `./dev.py publish` still bumps the patch. `clutch/release.py` only bumps in `clutch release`, and `./dev.py` has no `publish` task.

## Scope in / Scope out
In: edit only the sentences that make the four claims above false, in these three documents.
- `docs/roadmap-driver-plan.md`: the Status paragraph, the first item of section 6 and its closing paragraph about steps 1 and 2, the section 5 `vscode-publish` sentence, the `publish` row of "Where each piece lives", and the Content cell of Ticket breakdown row 5 (`release-publish`). Section 5 should say the owner publishes the kept VS Code package by hand, per decision 20. The row 5 Content cell should drop `./dev.py vscode-publish` and note that decision 20 made Marketplace publishing manual.
- `docs/evidence-trail-plan.md`: the Status paragraph. Read the merged rows in `docs/roadmap.md` and the ticket folders to say which pieces are in effect and which remain planned.
- `docs/roadmap.md`: the section 1 prose sentence about `./dev.py publish`, and nothing else.

Out: decision 20 and the row text of merged rows (they record history and stay as written). Rows 104 and 124 in `docs/roadmap.md` keep their text, even though it mentions `dev.py publish`. Every code, test and spec file. `CLUTCH_PLAN.md`. No new check or lint; file a Suggestion Box entry if one seems worth it.

## Scope fence
- docs/roadmap-driver-plan.md
- docs/evidence-trail-plan.md
- docs/roadmap.md

## Acceptance criteria
1. `grep -n 'vscode-publish' docs/roadmap-driver-plan.md` prints nothing and exits 1. It must not still name the dropped task in section 5, "Where each piece lives", or the Ticket breakdown row 5.
2. `sed -n '/^## 1\. Release plan/,/^## 2\./p' docs/roadmap.md | grep -n 'dev.py publish'` prints nothing and exits 1. Section 1 must not say `./dev.py publish` bumps the patch. Rows 104 and 124 keep their text, so this check is limited to section 1.
3. `grep -n -i 'remain planned\|remains roadmap row\|still planned' docs/roadmap-driver-plan.md` prints no line about the idle-point supervisor hook or row 108. Status and section 6 must not call them planned.
4. `grep -n 'Nothing in it is in effect' docs/evidence-trail-plan.md` prints nothing and exits 1. The Status paragraph names the merged rows and the still-open `evidence-rusage-capture`.
5. `git diff --stat main -- . ':!docs/roadmap-driver-plan.md' ':!docs/evidence-trail-plan.md' ':!docs/roadmap.md'` prints nothing, so no file outside the fence changes.
6. `./dev.py test tests/unit/test_roadmap_table.py tests/integration/test_roadmap_table.py` exits 0, so the roadmap table still parses and the plan paths still resolve.

## Verification
```
./dev.py test tests/unit/test_roadmap_table.py tests/integration/test_roadmap_table.py
```

## Definition of rejected
A branch is rejected if it changes any file outside the three documents, rewrites decision 20 or merged-row history, or leaves any of the four stale claims in place, even if the tests pass.

## Time budget
- expected: 25m
- stuck: 50m
