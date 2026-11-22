---
state: confirmed
source: human
priority: P1
kind: feature
---

## Depends on
- training-triage-records
- serve-flaky-tests-deterministic
- serve-live-keep-single-verdict

## Context
- clutch/training.py::report
- clutch/__main__.py::_parser
- clutch/config.py::TrainingData
- tests/unit/test_main_evidence_captures.py
- tests/integration/test_roadmap_gate.py::test_real_roadmap_gate_blocks
- clutch/docs/host-training.md#Enable it
- clutch/docs/host-training.md#Export

## On-demand
- docs/roadmap.md
- clutch/docs/host-running.md
- docs/how-clutch-works.md

## Goal / Why
Section 1 of `docs/roadmap.md` ships 0.5.0 only when `training export` produces every record kind from this repo's journal, and the 0.5.0 `gate` block has no command for that clause. Two facts block it today. `config.yaml` has no `training_data` entry, so `clutch training export` refuses (`TrainingData.require_enabled`), and only attempts after enabling carry a diff. And `training export` exits 0 whatever it wrote: `handle_training` prints the counts and returns 0 even when every count is 0, so no existing invocation proves a kind has a record, and a gate on exit 0 alone would pass vacuously.

When this is done, `config.yaml` has `training_data: {enabled: true}`, `clutch training export` takes a flag `--require-records` that, after writing the files and printing the report, exits 2 with a Refusal naming every requested kind whose count is 0, and the 0.5.0 `gate` block runs an export of all seven kinds (`implement`, `preference`, `review`, `diagnosis`, `ticket`, `conflict`, `triage`) with that flag, so the gate passes only when each kind has at least one record.

Honest limit: the gate can fail in the live checkout until the journal holds a record of every kind (implement and preference records need attempt diffs, which exist only for attempts after `training_data.enabled` was set; conflict records need a past conflict-rerun). That is the clause's meaning, not a defect; the gate's first run after merge reports which kinds are missing.

Ordering: `training-triage-records` must merge first, because the `triage` kind exists only after it. `training-eval-ship-gate` needs `training_data` enabled and edits the same `gate` block, so this ticket must merge before it (that ticket lists this one under `## Depends on`).

## Boundary contract
### training export exit contract
- disposition: extend
- owner: clutch/__main__.py (the `training export` parser and `handle_training`); `clutch/training.py::render` and `report` are unchanged
- consumers: the 0.5.0 gate block via `clutch roadmap gate`, operators running `clutch training export`
- observable change: new flag `--require-records` (default off). When set, after files are written and the report printed, a requested kind whose count is 0 makes the command raise `runner.Refusal` (exit 2) naming each such kind and the road "run more tickets with training_data.enabled, or drop the kind from --kinds"; when every requested kind has at least one record it exits 0. Without the flag the exit code is unchanged.
- compatibility: existing flags, defaults, written files and report lines are unchanged; a run without the flag behaves as before
- acceptance: criteria 1-3
- tests: tests/unit/test_training_export_require_records.py
- post-merge source of truth: clutch/__main__.py and the `exits` text of the `export` command help

### Training data switch
- disposition: reuse
- owner: config.yaml (`training_data`), schema `clutch/config.py::TrainingData`
- consumers: `clutch training export`, `clutch training eval`, harvest (attempt manifests carry diffs only when enabled)
- observable change: the live config enables the existing key; no schema change
- compatibility: `TrainingData.enabled` default stays false for every other host
- acceptance: criterion 4
- tests: tests/integration/test_roadmap_gate.py parses the new command's arguments; the config loading is the existing `Config` schema
- post-merge source of truth: config.yaml

### 0.5.0 ship gate block
- disposition: extend
- owner: docs/roadmap.md (the `gate` block under `### 0.5.0`, parsed by `clutch/roadmap.py::gates`)
- consumers: `clutch roadmap gate 0.5.0`, `clutch roadmap status`, the roadmap driver
- observable change: one added argv command between `uv run clutch meta check docs clutch/docs tests` and `./dev.py test`, and the sentence under the 0.5.0 table that lists unchecked ship clauses stops naming the export clause
- compatibility: the first, last two and existing commands keep their positions and form
- acceptance: criterion 5
- tests: `tests/integration/test_roadmap_gate.py::test_real_roadmap_gate_blocks` parses the real block and each command's arguments
- post-merge source of truth: docs/roadmap.md

## Scope in / Scope out
Scope in:
- `clutch/__main__.py`: add `--require-records` (`store_true`) to the `export` parser; in `handle_training`, after the report prints, raise `runner.Refusal` when the flag is set and any kind in `args.kinds` has `counts[kind] == 0`; update the `export` command's `exits` text ("0 on success; 2 when disabled or refused") to name this case and add the flag to its `examples`. Only these edits change in that file.
- `config.yaml`: add the single top-level key `training_data: {enabled: true}`; no other line changes (the file is the owner's live configuration and other tickets edit it).
- `docs/roadmap.md`: under `### 0.5.0`, add `uv run clutch training export --out .clutch/training-export --kinds implement preference review diagnosis ticket conflict triage --require-records` to the `gate` block after the `meta check` line and before `./dev.py test`. Edit the sentence after the 0.5.0 table (`The remaining 0.5.0 ship clauses are unchecked: ...`) to drop the export clause only. Edit nothing else there: not section 1, not row 203's text.
- `clutch/docs/host-training.md` (Export: the flag and its exit 2), `clutch/docs/host-running.md` (`training export` row) and `docs/how-clutch-works.md` (section 2 `training export` row): name `--require-records` and its exit 2.
- A new unit test file `tests/unit/test_training_export_require_records.py` with a `clutch:meta` header from `uv run clutch meta refresh` (edit only `purpose`; refresh needs the engine lock, so run it when serve is stopped, or the implementing worktree runs it). It drives `main(["training", "export", ...], cwd=tmp_path)` as `tests/unit/test_main_evidence_captures.py` does.
- `tests/integration/test_roadmap_gate.py` needs no edit: it already exempts `0.5.0` from the three-command count and parses every command's arguments.
Scope out: `training-eval-ship-gate` (the eval command and its exit contract; it merges after this ticket); `clutch/training.py` (kinds and counts are unchanged; `triage` arrives with `training-triage-records`); changing default `--kinds`; making the flag the default; any plan document.

## Scope fence
- clutch/__main__.py
- config.yaml
- docs/roadmap.md
- clutch/docs/host-training.md
- clutch/docs/host-running.md
- docs/how-clutch-works.md
- tests/unit/test_training_export_require_records.py

## Acceptance criteria
1. With training enabled and an empty evidence store, `main(["training", "export", "--out", ..., "--require-records"], cwd=tmp_path)` prints the report, returns 2, and stderr names every requested kind; the same call without the flag returns 0, not 2; checked by `./dev.py test tests/unit/test_training_export_require_records.py`.
2. With a requested kind at count 0 and another above 0, the flag still exits 2 and names only the zero kind, not the populated one; with every requested kind above 0 it exits 0, not 2 (counts supplied by a fake `render`); checked by `./dev.py test tests/unit/test_training_export_require_records.py`.
3. `--require-records` is accepted by the parser, defaults to false, and the formatted `training export` help names it and the exit 2 case; checked by `./dev.py test tests/unit/test_training_export_require_records.py tests/unit/test_main_help.py tests/unit/test_main_training_group.py`.
4. `config.yaml` loads with `training_data.enabled` true, not false; checked by `uv run python -c "from pathlib import Path; from clutch.config import load_config; print(load_config(None, cwd=Path('.')).training_data.enabled)"` printing `True`.
5. The 0.5.0 `gate` block parses with the export command in the order above, its `--kinds` list names all seven kinds, the other releases' blocks are unchanged, and every command's arguments parse; checked by `./dev.py test tests/integration/test_roadmap_gate.py`. The three docs naming the flag is a one-time review check.

## Verification
```
./dev.py test tests/unit/test_training_export_require_records.py tests/unit/test_main_help.py tests/unit/test_main_training_group.py tests/unit/test_training_config.py tests/integration/test_roadmap_gate.py
uv run clutch ticket lint training-export-ship-gate
```

## Definition of rejected
The branch is rejected if it makes a run without `--require-records` exit non-zero, adds the flag to the default behavior, changes `clutch/training.py` or default `--kinds`, edits any `config.yaml` line other than adding `training_data`, edits the eval command or its gate line, adds a standing test pinning roadmap text beyond the gate-block parse, adds tests to a hot test file, or passes the gate vacuously on an empty export.

## Time budget
- expected: 25m
- stuck: 50m
