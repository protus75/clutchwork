---
state: confirmed
source: box:roadmap_row
priority: P1
kind: chore
---

## Depends on
none

## Context
- docs/evidence-trail-plan.md#Status
- docs/roadmap-driver-plan.md#Current state

## Goal / Why
Two plan documents still describe merged work as open. `docs/evidence-trail-plan.md` Status says resource usage capture remains open as `evidence-rusage-capture`, but row 123 merged and `clutch/providers.py::CliAdapter.invoke` records rusage. `docs/roadmap-driver-plan.md` Current state, in the release tooling bullet, says `./dev.py vscode-package` builds a `.vsix` and prints the Marketplace upload page for a hand upload, but `clutch/release.py::run_packages` keeps the package at ship (row 108). This replaces merged row 143, which missed these claims. After this change both documents name what merged, so the next audit starts clean.

## Scope in / Scope out
Scope in:
- In `docs/evidence-trail-plan.md` Status, move resource usage capture from open to merged. Cite roadmap row 123 and `evidence-rusage-capture`. Keep the sentence that the evidence verbs, per-attempt spool move and parser consolidation remain planned (rows 62-64).
- In `docs/roadmap-driver-plan.md` Current state, in the release tooling bullet only, replace the sentence that `./dev.py vscode-package` prints the Marketplace upload page for a hand upload. State that the VSIX is a configured release package that `clutch/release.py::run_packages` builds and keeps at ship (row 108). Read `clutch/release.py` and the `release.packages` config first, so the new wording matches the code.

Scope out: every other section and bullet of both documents, code, and tests.

## Scope fence
- docs/evidence-trail-plan.md
- docs/roadmap-driver-plan.md

## Acceptance criteria
1. `docs/evidence-trail-plan.md` Status no longer says rusage capture "remains open". `git grep -n "remains open as" docs/evidence-trail-plan.md` prints nothing, and `git grep -n "row 123" docs/evidence-trail-plan.md` finds the merged claim.
2. The planned-work sentence is kept. `git grep -n "rows 62" docs/evidence-trail-plan.md` still matches.
3. `docs/roadmap-driver-plan.md` no longer calls the VSIX a hand upload. `git grep -n "hand upload" docs/roadmap-driver-plan.md` prints nothing, and `git grep -n "run_packages" docs/roadmap-driver-plan.md` matches.
4. The roadmap parser tests still pass: `./dev.py test tests/unit/test_roadmap_table.py`.

## Verification
```
git grep -n "row 123" docs/evidence-trail-plan.md
git grep -n "run_packages" docs/roadmap-driver-plan.md
./dev.py test tests/unit/test_roadmap_table.py
```

## Definition of rejected
Any edit outside the two fenced documents, any change to a section other than the named ones, or a claim about `run_packages` or rusage that the code does not support.

## Time budget
- expected: 8m
- stuck: 16m
