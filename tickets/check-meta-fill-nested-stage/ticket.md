---
state: confirmed
source: human
priority: P0
kind: bug
---

## Depends on
- none

## Context
- clutch/driver.py::Driver.stage
- clutch/driver.py::Driver._run
- clutch/metafill.py::make_ask
- clutch/stages.py::check_meta
- tests/unit/test_driver_check_nesting.py

## Goal / Why
On 2026-11-22 at 02:11:57Z `engine serve` stopped with `error: ValueError` (evidence `serve-crash.log`). `serve-flaky-tests-deterministic` had entered Check, and Check's `check_meta`, added by `check-owns-meta-headers` (a7469ec2), filled `clutch:meta` purposes by calling `metafill.make_ask`. That runs `Driver.run` with `ticket=None` and surface `meta`, so `Driver._run` opens `Driver.stage(stem="meta", surface="meta")` while `stages.py` holds `Driver.stage(stem=<ticket>, surface="check")` open. `Driver.stage` allows only `review_visual` (same stem) under `check`, so it raised `stage already open: stem=serve-flaky-tests-deterministic, surface=check`. The worker failure stopped serve and left two tickets interrupted. `meta.check` reports `drifted` for every edited file whose header hash no longer matches, so every Check whose diff edits a file under the configured meta paths (`tests/`, `docs/`) hits this.

When this ticket is done, the ticketless meta stage (stem `meta`, surface `meta`) may open inside any open `check` stage. Every other nesting is still refused exactly as today.

## Boundary contract
### Driver stage nesting
- disposition: extend
- owner: clutch/driver.py
- consumers: stages.run_stages (Check), stages.check_meta through metafill.make_ask, runner merge stage, Driver._run
- observable change: `Driver.stage(stem="meta", surface="meta")` opened while any `(<stem>, "check")` stage is open no longer raises; on exit the open stage reverts to the check stage
- compatibility: every nesting refused today stays refused, including `review` under `check`, `review_visual` under a different stem's `check`, and anything under `implement`; the existing `merge` and `review_visual` allowances are unchanged
- acceptance: criteria 1 to 3
- tests: tests/unit/test_driver_check_nesting.py and tests/regress_check_meta_nested_stage.py
- post-merge source of truth: clutch/driver.py

## Scope in / Scope out
Scope in: extend the nesting condition in `Driver.stage` in `clutch/driver.py` so that `(stem, surface) == ("meta", "meta")` is allowed when the open stage's surface is `check`. Add the case to `tests/unit/test_driver_check_nesting.py`. Add the carried reproducer `tests/regress_check_meta_nested_stage.py`.

Scope out: `metafill.py`, `stages.check_meta`, and how serve handles a worker exception. A worker ValueError stopping the whole serve process is a separate cause, filed separately. Do not add or edit `clutch:meta` headers by hand.

## Scope fence
- clutch/driver.py
- tests/unit/test_driver_check_nesting.py
- tests/regress_check_meta_nested_stage.py

## Acceptance criteria
1. Inside `Driver.stage(stem="work", surface="check")`, opening `Driver.stage(stem="meta", surface="meta")` does not raise, and after it exits `_open_stage` is `("work", "check")`, not `None` or `("meta", "meta")`; checked by `./dev.py test tests/unit/test_driver_check_nesting.py`.
2. `Driver.stage(stem="meta", surface="meta")` opened inside `Driver.stage(stem="work", surface="implement")` still raises `stage already open`; checked by `./dev.py test tests/unit/test_driver_check_nesting.py`.
3. The existing refusals in `test_check_nesting_restores_and_restricts` (`review` under `check`, `review_visual` under another stem's `check`) still raise; checked by `./dev.py test tests/unit/test_driver_check_nesting.py`.
4. `uv run python tests/regress_check_meta_nested_stage.py` prints `{"regression_result": "pass"}` and exits 0 on the branch, and prints `{"regression_result": "defect"}` with a non-zero exit on the merge base.

## Verification
```
uv run python tests/regress_check_meta_nested_stage.py
./dev.py test tests/unit/test_driver_check_nesting.py tests/unit/test_check_meta_fill.py
```

## Definition of rejected
- The fix lets any surface open under `check`, or drops the stem match for `review_visual`.
- The fix moves or removes the meta fill from Check instead of allowing the nesting.
- Any edit outside the fence.

## Time budget
- expected: 8m
- stuck: 16m

## Regression
```
uv run python tests/regress_check_meta_nested_stage.py
```
- carries: tests/regress_check_meta_nested_stage.py
