---
priority: P3
kind: feature
agent_tier: medium
agent_effort: medium
source: box:roadmap_row
state: confirmed
---

## Depends on
- training-export-kinds

## Context
- docs/training-data-plan.md#3. Export: training records
- clutch/training.py
- clutch/__main__.py::_command
- clutch/llmeffect.py::scoped_seq
- clutch/mergequeue.py::ResolveReply
- tests/unit/test_training_ticket_kind.py
- tests/unit/test_training_export_kinds.py
- tests/unit/test_main_training_group.py

## On-demand
- docs/how-clutch-works.md
- clutch/docs/host-running.md
- clutch/docs/host-training.md

## Goal / Why
`clutch training export` today counts stems that have a `resolve`-surface call as `conflict skipped` and writes no conflict file. After this ticket `--kinds conflict` writes `conflict.jsonl`, one chat-message record per `resolve` call whose reply resolved the conflict, so a host can tune a small model on its own merge-conflict resolutions. `merge-model-resolve` has merged, so the calls exist (`clutch/mergequeue.py::_model_resolve`).

Record shape: `{"messages": [{"role": "user", "content": <the call's prompt blob>}, {"role": "assistant", "content": <the call's reply text>}], <identity fields>}` with `kind` `conflict`, `stem` from the call key, `call_keys` `[key]`, and label `merged` when the stem is a merged ticket, otherwise `neutral`. Resolve calls are keyed with a scoped run sequence (`clutch/llmeffect.py::scoped_seq`, for example `resolve2<sha>-1`), so the record's `run_seq` is that string as keyed, not an integer; the existing `_calls` and `_identity` convert `run_seq` with `int()` and would skip these calls, so the conflict path must not use them unchanged. The reply text is decoded from the call's `end` record with the same adapter normalizer the `ticket` kind uses. A reply whose JSON `verdict` is not `resolved` (a `decline`), or whose call has no readable `end` record, prompt blob or valid JSON, is skipped and counted in `skipped`. The conflict count replaces the `conflict skipped` count.

The plan's "merged green or not" label is approximated by whether the stem merged, the same rule `diagnosis` and `ticket` use; a finer label needs a source no code provides.

Why: plan section 3 lists `conflict` as an export kind that exists once `merge-model-resolve` has merged; roadmap row 177 asks for it.

## Boundary contract
### Training export
- disposition: extend
- owner: clutch/training.py
- consumers: the `clutch training export` handler in `clutch/__main__.py`; operators reading `training export` output
- observable change: `render` also builds a `conflict` kind when requested and writes `conflict.jsonl`; its counts replace `conflict_skipped` with `conflict`, and `report` prints `conflict: N` in that place. Failures: a decline reply, missing end record, missing prompt blob or non-JSON reply skips the record and counts in `skipped`; the same second scrub (`_safe`) drops a record whole and counts it in `dropped`. Ordering: conflict records sort by `(stem, run_seq, attempt)` with `run_seq` a string, so two exports of the same sources are byte-identical. Held-out stems write no conflict record, and `since` filters by the call's `clock.wall_start`. When the kind is not requested no `conflict.jsonl` is written.
- compatibility: `implement`, `preference`, `review`, `diagnosis` and `ticket` records and files keep their shape; the default `--kinds` stays the same four kinds, so a default export does not write `conflict.jsonl`. The `conflict_skipped` key is removed and every reader is updated in this change (the `report` function and the three test sites that build counts).
- acceptance: criteria 1-5.
- tests: tests/unit/test_training_export_conflict.py
- post-merge source of truth: clutch/training.py

### Command surface
- disposition: extend
- owner: clutch/__main__.py (`training export` parser and help)
- consumers: operators, `tests/unit/test_main_help.py`, `tests/unit/test_host_running.py`
- observable change: `--kinds` also accepts `conflict`; the help and the two verb tables name it.
- compatibility: existing flags, the default kinds and exit codes are unchanged.
- acceptance: criterion 6.
- tests: tests/unit/test_main_training_group.py
- post-merge source of truth: clutch/__main__.py

## Scope in / Scope out
Scope in:
- `clutch/training.py`: the `conflict` kind, the `conflict` count replacing `conflict_skipped` (counts dict and `report`). Pull the ticket loop's reply-text decoding (normalizer, last assistant message, Gemini concatenation) into one helper that both `ticket` and `conflict` call, with the `ticket` behavior unchanged; this is the one shared helper and two callers earn it.
- `clutch/__main__.py`: add `conflict` to the `--kinds` choices and to the `export` help text. Leave the default list alone.
- `tests/unit/test_training_export.py` and `tests/unit/test_training_ticket_kind.py`: change only the `conflict_skipped=0` keyword in the counts dicts passed to `training.report` to `conflict=0`.
- `tests/unit/test_training_export_kinds.py`: change only the two assertions at the end of `test_since_conflict_holdout_and_scrub` that expect `conflict_skipped == 2` and `conflict skipped: 2`; they now assert the default and the `review`/`diagnosis` kinds write no `conflict.jsonl` and the counts report `conflict: 0`.
- `tests/unit/test_main_training_group.py`: change only the rejected-kinds list (drop `conflict`) and add an assertion that `--kinds conflict` is accepted and the default is unchanged.
- `docs/how-clutch-works.md` section 2 `training export` row, `clutch/docs/host-running.md` `training export` row and `clutch/docs/host-training.md` kinds sentence: name `conflict`.

Scope out: the `triage` kind; `training eval`; `clutch/evidence/`; the attempt manifest writer; the merge path in `clutch/mergequeue.py`; a finer-than-merged label.

## Scope fence
- clutch/training.py
- clutch/__main__.py
- clutch/docs/host-running.md
- clutch/docs/host-training.md
- docs/how-clutch-works.md
- tests/unit/test_training_export_conflict.py
- tests/unit/test_training_export.py
- tests/unit/test_training_ticket_kind.py
- tests/unit/test_training_export_kinds.py
- tests/unit/test_main_training_group.py

## Acceptance criteria
1. With `kinds=("conflict",)`, a `resolve` call keyed `llm/s/resolve2abc-1/resolve/1/1` whose reply is `{"verdict": "resolved", ...}` yields one record with `kind` `conflict`, `run_seq` equal to the string `resolve2abc-1`, user content equal to the prompt blob, assistant content equal to the reply text, and label `merged` for a merged stem and `neutral` otherwise; the call is not silently skipped by an integer `run_seq` conversion; checked by `./dev.py test tests/unit/test_training_export_conflict.py`.
2. A `decline` reply, a call with no `end` record, and a non-JSON reply each write no record and add 1 each to `skipped`, not an empty-content record; checked by `./dev.py test tests/unit/test_training_export_conflict.py`.
3. `since="2026-11-10"` drops a conflict call whose `wall_start` is `2026-11-09T23:59:59Z` and keeps one on `2026-11-10`; checked by `./dev.py test tests/unit/test_training_export_conflict.py`.
4. A held-out stem (`holdout=100`) writes no conflict record, and a record whose prompt holds a `Bearer` token of 20 or more characters is dropped and counted in `dropped`, not truncated; checked by `./dev.py test tests/unit/test_training_export_conflict.py`.
5. Without `conflict` in `kinds`, no `conflict.jsonl` is returned and `counts` has `conflict` equal to 0 and no `conflict_skipped` key; `training.report` output contains `conflict: 1` for a count of 1 and never `conflict skipped`; checked by `./dev.py test tests/unit/test_training_export_conflict.py tests/unit/test_training_export.py tests/unit/test_training_export_kinds.py`.
6. `--kinds conflict` parses to `["conflict"]`, `--kinds bogus` still exits 2, the default kinds list is still `["implement", "preference", "review", "diagnosis"]`, and the formatted `training export` help contains `conflict`; checked by `./dev.py test tests/unit/test_main_training_group.py`.
7. The `ticket` kind output is unchanged by the helper extraction, and the help and run-guide tables still pass; checked by `./dev.py test tests/unit/test_training_ticket_kind.py tests/unit/test_main_help.py tests/unit/test_host_running.py`.

## Verification
```
./dev.py test tests/unit/test_training_export_conflict.py tests/unit/test_training_export.py tests/unit/test_training_export_kinds.py tests/unit/test_training_ticket_kind.py tests/unit/test_training_trajectory.py tests/unit/test_main_training_group.py tests/unit/test_main_help.py tests/unit/test_host_running.py
```

## Definition of rejected
The branch keeps a `conflict_skipped` count beside `conflict`, writes a record from a decline or partly built call, writes a record for a held-out stem, converts the scoped `run_seq` to an integer, adds `conflict` to the default kinds, adds a `./dev.py` wrapper, or edits a file outside the fence.

## Time budget
- expected: 20m
- stuck: 40m
