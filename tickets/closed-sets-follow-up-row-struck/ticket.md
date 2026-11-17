---
state: confirmed
source: human
priority: P0
kind: bug
---

## Depends on
none

## Context
- tickets/closed-sets-follow-up-row-struck/evidence/failure.txt
- tests/integration/test_closed_sets_single_owner.py
- clutch/roadmap.py::parse
- clutch/roadmap.py::strike
- clutch/roadmap.py::link
- docs/roadmap.md
- tests/regress_already_satisfied.py

## Goal / Why
Main is red. `tests/integration/test_closed_sets_single_owner.py::test_follow_up_row` (merged with `closed-sets-single-owner`) matches raw row text in the live `docs/roadmap.md`: `^\| 19 \| `closed-sets-single-owner` \|`. The roadmap driver strikes a row's stem (`~~` around it) and rewrites its Content prefix (`**Authored**`, `**Merged**`) in its own commits after a merge, so the driver's strike of row 19 (`df4ce0ae`) made the test fail on main for every later ticket (evidence: `tickets/closed-sets-follow-up-row-struck/evidence/failure.txt`; box-000597 and box-000598 report it from `roadmap-held-row-refile`). The release gate runs the full suite, so 0.3.0 cannot ship while it fails. The same test also breaks once the driver links or strikes row 49 (`graphics-kind`) or the `closed-sets-remaining` row.

After this change the test reads the roadmap's rows through `clutch.roadmap.parse`, which strips the strike marks and exposes each row's stem, owner, kind, priority and Depends on, so the driver's link and strike edits never change its result.

## Scope in / Scope out
In:
- `tests/integration/test_closed_sets_single_owner.py::test_follow_up_row`: parse the roadmap file at `clutch.roadmap.ROADMAP` with `clutch.roadmap.parse` and assert on `Row` fields instead of raw line text. It keeps every fact it checks today: exactly one row has stem `closed-sets-remaining`; its release name (`clutch.roadmap.release_name`) is `0.3.0`; its owner is `roadmap`, kind `chore`, priority `P3`, and `clutch.roadmap.depends_on` gives `("closed-sets-single-owner",)`; row 19's stem is `closed-sets-single-owner`; row 49's stem is `graphics-kind` and its Depends on includes `closed-sets-single-owner`. The raw-text `section` split and the three `re` patterns go.
- New `tests/regress_closed_sets_follow_up_row.py`: the regression reproducer below.

Out: the roadmap document itself (never edited to make a test pass), the other tests in the file, and `clutch/roadmap.py`.

## Scope fence
- tests/integration/test_closed_sets_single_owner.py
- tests/regress_closed_sets_follow_up_row.py

## Acceptance criteria
1. `./dev.py test tests/integration/test_closed_sets_single_owner.py` exits 0 on the branch, with row 19 struck as it is on main. Ruled out: a test that still fails on the driver's strike.
2. `tests/integration/test_closed_sets_single_owner.py::test_follow_up_row` calls `clutch.roadmap.parse` and asserts on `Row` fields (`stem`, `owner`, `kind`, `priority`, `release`, and `depends_on`), with no `re` pattern over raw row text; reading the test shows this. Ruled out: a fix that only adds `~~` to one regex and still breaks when the driver links or strikes row 49 or the `closed-sets-remaining` row.
3. `uv run python tests/regress_closed_sets_follow_up_row.py` prints `{"regression_result": "pass"}` and exits 0 on the branch. It runs `test_follow_up_row` in a pytest subprocess (`sys.executable -m pytest -q -p no:cacheprovider <that node id>`) from the repo root: exit 0 prints `pass` and exits 0, exit 1 prints `defect` and exits 1, and anything else, including a missing test file, prints `error` and exits 2. It prints exactly one JSON object to stdout, with diagnostics on stderr.

## Verification
```
./dev.py test tests/integration/test_closed_sets_single_owner.py
uv run python tests/regress_closed_sets_follow_up_row.py
./dev.py test
```

## Definition of rejected
The branch is rejected if it edits `docs/roadmap.md` or any file outside `## Scope fence`, drops any fact `test_follow_up_row` checks today, or leaves a raw-text pattern over a roadmap row in `test_follow_up_row`.

## Time budget
- expected: 15m
- stuck: 45m

## Regression
```
uv run python tests/regress_closed_sets_follow_up_row.py
```
- carries: tests/regress_closed_sets_follow_up_row.py
