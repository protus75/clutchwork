---
state: rejected
source: human
priority: P2
kind: bug
---

## Depends on
- none

## Context
- clutch/observe.py::snapshot
- vscode-clutchwork/media/view.js
- vscode-clutchwork/media/view.css
- tests/integration/test_hot_paths_snapshot.py
- tests/regress_already_satisfied.py

## Goal / Why
The extension's Tickets view draws each hot-path entry and each verdict-decision entry as a bare `div` with the class `status`, above the ticket rows and with no heading. `status` is the class for a ticket's status text, so a line such as `clutch/__main__.py: 2` looks like an error message floating above the tickets and nothing says what it is (owner report, 2026-11-20; evidence file). After this ticket each of the two groups is drawn under a heading, taken from a snapshot field, that says what the group is, and its rows use their own class, not `status`. When a group is empty its heading is not drawn.

Why: a person reading the view cannot tell contended-path counts from a failure, and the heading text is a fact clutch owns, so it comes from the snapshot, not from the JavaScript.

## Boundary contract
### Tickets view group headings
- disposition: extend
- owner: clutch/observe.py
- consumers: the Tickets view in vscode-clutchwork/media/view.js
- observable change: the snapshot gains `hotPathsLabel` and `verdictDecisionsLabel`, each a non-empty string; the view draws a heading with that text above its group when the group has rows, and draws the group rows with a new `group-row` class instead of `status`
- compatibility: preserves every existing snapshot field, the row text (`<path>: <count>` and the decision line), the hover help and the ticket rows; a snapshot shape change updates its JavaScript reader in the same change
- acceptance: the snapshot carries both label fields as non-empty strings and the JavaScript no longer builds these rows with the `status` class
- tests: tests/unit/test_observe_group_labels.py, tests/integration/test_snapshot_group_labels.py
- post-merge source of truth: clutch/observe.py

## Scope in / Scope out
In: clutch/observe.py defines module constants `HOT_PATHS_LABEL` ("Paths fenced by two or more unsettled tickets") and `VERDICT_DECISIONS_LABEL` ("Verdict decisions"), and `snapshot` returns them as `hotPathsLabel` and `verdictDecisionsLabel`. Create tests/unit/test_observe_group_labels.py, which imports the two constants and asserts each is a non-empty string. `render` in vscode-clutchwork/media/view.js puts a `group-label` heading element, with the label text from the snapshot, before each non-empty group, and draws the group's rows with the class `group-row`. vscode-clutchwork/media/view.css gains `.group-label` (small, bold, `--vscode-sideBarSectionHeader-foreground`) and `.group-row` (normal foreground, not the dimmed `status` colour). The JavaScript adds no text of its own and filters nothing. Create tests/integration/test_snapshot_group_labels.py, which builds a snapshot with the rig used by tests/integration/test_hot_paths_snapshot.py and asserts both label fields are non-empty strings. Create tests/regress_hot_paths_labeled_section.py, the carried reproducer, shaped like tests/regress_already_satisfied.py: it builds a snapshot and prints only `{"regression_result": "pass"}` with exit 0 when `hotPathsLabel` is a non-empty string, `{"regression_result": "defect"}` with exit 1 when the key is missing or empty, and `{"regression_result": "error"}` with exit 2 on an exception (traceback to stderr).

Out: the hot-paths filter (merged in `hot-paths-only-contended`), help entries, the Box and Details views, and `docs/how-clutch-works.md`.

## Scope fence
- clutch/observe.py
- vscode-clutchwork/media/view.js
- vscode-clutchwork/media/view.css
- tests/integration/test_snapshot_group_labels.py
- tests/unit/test_observe_group_labels.py
- tests/regress_hot_paths_labeled_section.py

## Acceptance criteria
1. `observe.snapshot` returns `hotPathsLabel` and `verdictDecisionsLabel` as non-empty strings, not missing keys, checked by `./dev.py test tests/unit/test_observe_group_labels.py tests/integration/test_snapshot_group_labels.py`.
2. The existing hot-paths snapshot expectations still hold, checked by `./dev.py test tests/integration/test_hot_paths_snapshot.py`.
3. The carried reproducer prints `{"regression_result": "pass"}` on the branch head, checked by `uv run python tests/regress_hot_paths_labeled_section.py`.
4. The snapshot's other fields are unchanged, checked by `./dev.py test tests/integration/test_hot_paths_snapshot.py`.

## Verification
```
./dev.py test tests/unit/test_observe_group_labels.py tests/integration/test_snapshot_group_labels.py tests/integration/test_hot_paths_snapshot.py
uv run python tests/regress_hot_paths_labeled_section.py
```

## Definition of rejected
- The heading text is written in JavaScript instead of read from the snapshot.
- The JavaScript filters, sorts or derives rows.
- An empty group still draws its heading.

## Time budget
- expected: 15m
- stuck: 30m

## Regression
```
uv run python tests/regress_hot_paths_labeled_section.py
```
- carries: tests/regress_hot_paths_labeled_section.py
