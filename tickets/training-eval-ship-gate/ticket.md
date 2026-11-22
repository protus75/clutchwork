---
state: confirmed
source: human
priority: P1
kind: feature
---

## Depends on
- training-export-ship-gate

## Runs before
- drain-retro-check-once-per-settle

## Context
- clutch/training.py::evaluate
- clutch/training.py::report_eval
- clutch/__main__.py::_parser
- clutch/roadmap.py::gates
- clutch/roadmap.py::run_gate
- tests/integration/test_roadmap_gate.py::test_real_roadmap_gate_blocks
- tests/unit/test_training_eval.py
- clutch/docs/host-training.md#Evaluate a review route

## On-demand
- docs/roadmap.md

## Goal / Why
Section 1 of `docs/roadmap.md` ships 0.5.0 only when `training eval` scores one lens, but the 0.5.0 `gate` block has no command for that clause. Today `clutch training eval` exits 0 even when it scored nothing: `training.evaluate` returns `total: 0, agreement: 0.00%` for an empty holdout and counts every reply it cannot parse as `unparsed`, and `__main__.py` prints the report and returns 0 either way. So no existing invocation can prove a score exists on held-out records, and a gate on exit 0 would pass vacuously.

When this is done, `training eval` exits 2 with a Refusal when no held-out review record received a parsed verdict (agree plus disagree equals 0), still printing the report first, and exits 0 only when at least one did. The 0.5.0 `gate` block gains two commands before `./dev.py test`: an export of the review kind with a holdout split into `.clutch/training-eval` (gitignored), then the review-lens eval reading that holdout file. The pair passes only when a held-out review record was scored.

Precondition: `training export` and `training eval` both refuse unless `training_data.enabled: true`. Row 203 `training-export-ship-gate` is a declared dependency; it has merged, set `training_data: {enabled: true}` in `config.yaml`, and added its command to the 0.5.0 `gate` block, so this ticket adds its commands to that block after row 203's.

## Boundary contract
### training eval exit contract
- disposition: extend
- owner: clutch/__main__.py (the `training eval` handler; `clutch/training.py::evaluate` unchanged)
- consumers: the 0.5.0 gate block via `clutch roadmap gate`, operators running `clutch training eval`
- observable change: exits 2 with a Refusal after printing the report when agree plus disagree is 0 (empty holdout, no review records for the held stems, or every reply unparsed); exits 0 otherwise as today
- compatibility: runs that score at least one record behave as before; the report line is byte-identical; only an unscored run changes from exit 0 to exit 2
- acceptance: criteria 1 and 2
- tests: a new unit test file driving the handler with fakes
- post-merge source of truth: clutch/__main__.py and the `exits` text of the `eval` command help

### 0.5.0 ship gate block
- disposition: extend
- owner: docs/roadmap.md (the `gate` block under `### 0.5.0`, parsed by `clutch/roadmap.py::gates`)
- consumers: `clutch roadmap gate 0.5.0`, `clutch roadmap status`, the roadmap driver
- observable change: two added argv commands between the `roadmap merged` command and `./dev.py test`
- compatibility: the first, `./dev.py test` and `roadmap accept` commands keep their positions and form
- acceptance: criterion 3
- tests: `tests/integration/test_roadmap_gate.py::test_real_roadmap_gate_blocks` parses the real block
- post-merge source of truth: docs/roadmap.md

## Scope in / Scope out
Scope in:
- `clutch/__main__.py`: in the `eval` handler, after `print(training.report_eval(...))`, raise `runner.Refusal` with a "no held-out review record was scored" message and the road "run training export with --kinds review and --holdout PCT, then pass its holdout.txt" when `agree + disagree == 0`; update the `eval` command's `exits` text (currently "0 on success; 2 when disabled, ...") to name this case. Only these edits change in that file.
- `docs/roadmap.md`: under `### 0.5.0`, add to the `gate` block after the `roadmap merged --release 0.5.0` line and before `./dev.py test`: `uv run clutch training export --out .clutch/training-eval --kinds review --holdout 20` and `uv run clutch training eval --route medium/review --holdout .clutch/training-eval/holdout.txt`. Edit only that block; do not edit section 1 or row 203's text. Mark nothing merged.
- `tests/integration/test_roadmap_gate.py`: the `len(commands) == 3` assertion exempts `0.4.0` today; it exempts `0.5.0` too (the one edit the longer block forces). Nothing else there changes.
- `docs/how-clutch-works.md` (section 2 `training eval` row) and `clutch/docs/host-running.md` (`training eval` row): add that eval exits 2 when it scored no held-out record. `clutch/docs/host-training.md` "Evaluate a review route": same sentence, and change "zero for no records" to say the run then exits 2.
- A new unit test file `tests/unit/test_training_eval_scored_exit.py` with a `clutch:meta` header from `uv run clutch meta refresh` (edit only `purpose`; refresh needs the engine lock, so run it when serve is stopped, or the implementing worktree runs it).
Scope out: `tests/integration/test_roadmap_table.py` (reads the real roadmap only for its table, not the gate block, so it is unchanged) and `tests/unit/test_supervise_idle_hooks.py` (touches `docs/roadmap.md` as an empty file and runs no eval, so it is unchanged); `config.yaml` (enabling `training_data` is row 203), `clutch/training.py`, the triage lens, any `training export` change.

## Scope fence
- clutch/__main__.py
- docs/roadmap.md
- tests/integration/test_roadmap_gate.py
- docs/how-clutch-works.md
- clutch/docs/host-running.md
- clutch/docs/host-training.md
- tests/unit/test_training_eval_scored_exit.py

## Acceptance criteria
1. `training eval` over a holdout whose stems yield no review records prints `total: 0, agree: 0, disagree: 0, unparsed: 0, agreement: 0.00%` and exits 2, not 0; checked by `./dev.py test tests/unit/test_training_eval_scored_exit.py`.
2. `training eval` where the model replies with no valid verdict for every record (`unparsed` equals `total`, agree and disagree 0) exits 2, not 0, and a run with one agreeing record still prints `total: 1, agree: 1, disagree: 0, unparsed: 0, agreement: 100.00%` and exits 0; checked by `./dev.py test tests/unit/test_training_eval_scored_exit.py` and the unchanged `./dev.py test tests/unit/test_training_eval.py`.
3. The 0.5.0 `gate` block parses with the export and eval commands in the order above, the other releases' blocks are unchanged, and every command's arguments parse; checked by `./dev.py test tests/integration/test_roadmap_gate.py`.
4. The `eval` command help `exits` text, the two `training eval` verb rows and `host-training.md` state the exit 2 case; checked by `./dev.py test tests/unit/test_main_help.py tests/unit/test_main_training_group.py`, and the doc sentences by review.

## Verification
```
./dev.py test tests/unit/test_training_eval_scored_exit.py tests/unit/test_training_eval.py tests/unit/test_main_help.py tests/unit/test_main_training_group.py tests/integration/test_roadmap_gate.py
uv run clutch ticket lint training-eval-ship-gate
```

## Definition of rejected
The branch is rejected if it edits `config.yaml`, changes `clutch/training.py::evaluate` or the report line, makes any scored run exit non-zero, adds a gate command that exits 0 on an empty or fully unparsed eval, adds a standing test pinning roadmap text beyond the gate-block parse, or adds tests to `tests/unit/test_training_eval.py`.

## Time budget
- expected: 25m
- stuck: 50m
