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
- docs/roadmap-driver-plan.md#Status
- docs/roadmap-driver-plan.md#Current state
- docs/evidence-trail-plan.md#Status
- docs/evidence-trail-plan.md#Current state
- clutch/seams.py::FileSystem

## On-demand
- docs/roadmap.md

## Goal / Why
After the 0.3.0 merges, six statements in three planning documents are false. When this ticket is done each one matches the code and the roadmap's own decisions, so the driver and agents that read these documents are not misled.

1. `docs/roadmap-driver-plan.md` Status says "Nothing in it is in effect". Its Current state says `./dev.py publish` bumps the patch version before upload, and that the supervising prompt never confirms or rejects. `clutch publish` now uploads only a version whose `v<version>` tag is on HEAD (row 92, merged). The drain-loop spec has the supervising agent loop run `confirm --yes` and `reject --yes` when a Recommendation says so (decision 19).
2. `docs/evidence-trail-plan.md` Current state says `_seq` resets to 0 per process and overwrites capture directories. Row 1 (`provider-capture-overwrite`) fixed that.
3. `docs/roadmap.md` section 3.2 says `FileSystem` has no `mkdir` or `remove`. `clutch/seams.py` now declares both (`fs-seam-mkdir-remove` merged).
4. `docs/roadmap.md` decision 5 (the CORE_TEMPLATE byte ledger) says 7,840 of 8,192 bytes are used. Row 103 states the template is 8,109 bytes today.
5. `docs/roadmap.md` decision 16 says the CORE_TEMPLATE change "waits in the Suggestion Box as box-000508". box-000508 was declined, and row 103 (`core-template-supervisor-verdicts`) owns the change.
6. `docs/roadmap.md` row 92 lists `./dev.py vscode-publish` (Marketplace). Decision 20 drops it: Marketplace publishing is the owner's manual step, and row 108 keeps the package.

## Scope in / Scope out
Scope in: edit only the sentences named above, in the section each lives in.
- `docs/roadmap-driver-plan.md`: the Status paragraph, and the Current state bullets on release tooling and on the supervising prompt. State what is merged and what is still draft, read from the merged tickets under `tickets/`. Leave the Departures table's record of the CORE_TEMPLATE rule alone, except to say box-000508 was declined and row 103 owns the change.
- `docs/evidence-trail-plan.md`: the Current state bullet about `_seq` resets and overwritten captures. Say row 1 fixed it. Keep the 3,944 and 2,453 counts as the measurement at `0895b5d4`.
- `docs/roadmap.md` (read it from the worktree; it is large): section 3.2's first sentence; the decision 5 ledger (use 8,109 bytes as the current figure, citing row 103); decision 16's last sentence; row 92's cell (drop the `./dev.py vscode-publish` clause, point to decision 20 and row 108). Keep the row's table shape so the parser still reads it.

Scope out: row 104's own cell (the driver strikes it when this merges); any code, test, spec, or CLAUDE.md/AGENTS.md change; other plans; any statement not named above; the CORE_TEMPLATE change itself (row 103).

## Scope fence
- docs/roadmap-driver-plan.md
- docs/evidence-trail-plan.md
- docs/roadmap.md

## Acceptance criteria
1. `grep -c 'Nothing in it is in effect' docs/roadmap-driver-plan.md` prints 0, and the Status section names which parts are merged (`grep -n '^## Status' -A4 docs/roadmap-driver-plan.md`).
2. `grep -c 'dev.py publish. bumps the patch' docs/roadmap-driver-plan.md` prints 0: the Current state no longer says the publish verb bumps the version before upload.
3. `grep -c 'waits in the Suggestion Box as box-000508' docs/roadmap-driver-plan.md docs/roadmap.md` prints 0 for each file. The text says box-000508 was declined and names row 103.
4. `grep -c '_seq. resets to 0' docs/evidence-trail-plan.md` prints 0 as a present-tense claim: the bullet says row 1 fixed it. A bullet that still reads "Capture directories are overwritten across processes" fails.
5. `grep -c 'has no .mkdir. or .remove.' docs/roadmap.md` prints 0, and section 3.2 says `FileSystem` has `mkdir` and `remove` (`grep -n 'mkdir' docs/roadmap.md`).
6. `grep -c '7,840 of 8,192' docs/roadmap.md` prints 0, and the decision 5 ledger states 8,109 bytes.
7. `grep -c 'vscode-publish' docs/roadmap.md` prints only the decision 20 mention, not row 92 (`grep -n 'vscode-publish' docs/roadmap.md` lists one line, in decision 20).
8. `./dev.py test tests/unit/test_roadmap_table.py tests/integration/test_roadmap_table.py` exits 0: the roadmap table still parses with the same row count and no row is lost or merged.

## Verification
```
./dev.py test tests/unit/test_roadmap_table.py tests/integration/test_roadmap_table.py tests/unit/test_roadmap_status.py tests/integration/test_roadmap_status.py
```

## Definition of rejected
The branch edits any file outside the three documents, changes row 104, edits CORE_TEMPLATE, `CLAUDE.md` or `AGENTS.md`, rewrites a section wholesale instead of the named sentences, or breaks the roadmap table parse.

## Time budget
- expected: 20m
- stuck: 40m
