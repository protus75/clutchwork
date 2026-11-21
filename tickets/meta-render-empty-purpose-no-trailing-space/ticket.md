---
state: draft
source: box:suggestion
priority: P0
kind: chore
agent_tier: medium
agent_effort: medium
---

## Depends on
none

## Context
- clutch/meta.py::_render
- clutch/meta.py::parse
- tests/unit/test_meta_refresh.py
- tests/unit/test_meta_cli.py

## Goal / Why
After this ticket, `meta.refresh` renders a new block's empty `purpose` as `# purpose:` (Python) or `purpose:` (Markdown) with no trailing space, so a freshly inserted block is already stable under `ruff format --check`. Today `_render` writes `purpose: ` with a trailing space. The Check step runs `check_meta` after `check_autofix` (clutch/stages.py), so nothing formats the inserted block, and ruff format then fails on it. Incident: serve-polls-block-parallel-runs attempt 2 failed Check only on the format gate, on line 5 of three new test files. `config.yaml` `meta.paths` covers `tests/`, so every ticket that adds a new .py test file is exposed to the same failure. This is an orchestration cause that breaks runs while it sits. Rendering without the trailing space is the minimum fix. Reordering Check steps is the rejected alternative: it changes the step order that other tests and docs pin, and the generator would still emit a line the formatter rewrites.

## Boundary contract
### Meta block rendering
- disposition: extend
- owner: clutch/meta.py
- consumers: `meta.refresh` and `meta.compose`, which are used by the Check step's `check_meta` and by `clutch meta refresh`; `meta.parse` and `meta.check` read the output
- observable change: a block with an empty field renders that line without trailing whitespace, for example `# purpose:`. Non-empty values render byte-identically to today.
- compatibility: `parse` splits on `:` and strips the value, so `purpose:` parses to an empty string and existing blocks with `purpose: ` still parse. `check` still reports `empty_purpose` for an empty purpose. The hash covers the body only, so it is unchanged.
- acceptance: refreshed output contains no line with trailing whitespace, and parsing it yields `purpose == ""`
- tests: tests/unit/test_meta_render_no_trailing_space.py
- post-merge source of truth: clutch/meta.py

## Scope in / Scope out
Scope in:
- In `clutch/meta.py::_render`, strip trailing whitespace from each rendered `key: value` line, for both the `.py` and `.md` forms.
- Add `tests/unit/test_meta_render_no_trailing_space.py`. It refreshes a new .py file and a new .md file through an in-memory fs, using the same MemoryFS pattern as `tests/unit/test_meta_refresh.py`. It asserts no line in either output ends in whitespace, and that `parse` returns an empty `purpose` and the original body.
- Update the two existing tests that pin the old trailing space: `tests/unit/test_meta_refresh.py` line 69 and `tests/unit/test_meta_cli.py` line 25. Each replaces `purpose: \n` with `purpose:\n`. This is the one expectation that changes in those files.

Scope out:
- The Check step order in `clutch/stages.py`.
- Reformatting existing files that already carry `purpose: ` with a trailing space.
- Any change to the schema or `parse`.

Class prevention: the new test asserts that no generated line has trailing whitespace, so any future generated field that renders empty fails it.

## Scope fence
- clutch/meta.py
- tests/unit/test_meta_render_no_trailing_space.py
- tests/unit/test_meta_refresh.py
- tests/unit/test_meta_cli.py

## Acceptance criteria
1. Refreshing a new .py file under a meta path produces a block whose every line satisfies `line == line.rstrip()`, not `# purpose: ` with a trailing space. Checked by `./dev.py test tests/unit/test_meta_render_no_trailing_space.py`.
2. Refreshing a new .md file produces the same no-trailing-whitespace result, and `meta.parse` of the output returns `fields["purpose"] == ""` and the original body, not `Malformed`. Checked by `./dev.py test tests/unit/test_meta_render_no_trailing_space.py`.
3. A block with a non-empty purpose still renders `# purpose: useful`, with exactly one space after the colon. Checked by `./dev.py test tests/unit/test_meta_render_no_trailing_space.py`.
4. `meta.check` on a freshly refreshed file reports `empty_purpose` and not `drifted` or `malformed`. Checked by `./dev.py test tests/unit/test_meta_cli.py`.
5. The existing meta tests pass with the updated expectation. Checked by `./dev.py test tests/unit/test_meta_refresh.py tests/unit/test_meta_cli.py tests/unit/test_meta_block.py tests/unit/test_meta_drift_check.py`.

## Verification
```
./dev.py test tests/unit/test_meta_render_no_trailing_space.py tests/unit/test_meta_refresh.py tests/unit/test_meta_cli.py tests/unit/test_meta_block.py tests/unit/test_meta_drift_check.py
```

## Definition of rejected
The branch is rejected if it reorders the Check steps instead of fixing the render, if `parse` stops accepting blocks that carry `purpose: ` with a trailing space, or if a test asserts only on the .py form.

## Time budget
- expected: 10m
- stuck: 20m
