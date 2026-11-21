---
state: draft
source: human
priority: P1
kind: feature
---

## Depends on
none

## Context
- docs/training-data-plan.md#3. Export: training records
- clutch/training.py::render
- clutch/training.py::report
- clutch/box.py::Message
- clutch/box.py::Verdict
- clutch/box.py::Resolution
- clutch/triage.py::TriageReply
- tests/unit/test_training_export_conflict.py

## On-demand
- clutch/docs/host-training.md

## Goal / Why
`clutch training export --kinds triage` writes `triage.jsonl`: one record per Triage model call, the user message being the call's prompt blob and the assistant message the call's reply text (a `TriageReply` JSON: verdict `author`, `tombstone` or `declined`). The plan (section 3, `triage` row) lists this kind and no code builds it, so a host cannot tune a small local model on its triage surface.

Triage calls are ticketless: the driver keys them `llm/triage/<message seq>/triage/<attempt>/<call>` (`stem = ticket or stage.surface`, `run_seq=message.seq` in `clutch/triage.py`). A record's `stem` is `triage`, its `run_seq` the message seq, and `group` follows `_identity`'s existing rule.

Label (operator override): the plan names `override_report` messages as the label source, but `clutch/box.py::Message` carries no field linking an override_report to a triaged message, so that source cannot be read. This ticket labels from the one override signal the box does record: the message with `seq == run_seq` has `status == "resolved"` and its `resolution.kind` disagrees with the reply verdict (verdict `author` maps to resolution kind `ticket`; `tombstone` and `declined` map to themselves). Disagreement is `negative`; agreement is `merged`; a pending message, or no message with that seq, is `neutral`. Owner decision needed if the plan's `override_report` linkage is still wanted: it needs a new link field on Message and is out of scope here.

Why: the plan's narrow, high-volume surfaces (triage, review, ticket) are the flywheel's first targets.

## Boundary contract
### Training export
- disposition: extend
- owner: clutch/training.py
- consumers: the `clutch training export` handler in `clutch/__main__.py`
- observable change: `render` accepts `triage` in `kinds` and takes a new keyword-only `box_messages` (default empty tuple) holding `Message` objects; it writes `triage.jsonl` only when requested; `counts` and `report` gain `triage`. A call whose reply is not valid JSON with a verdict in `author`, `tombstone`, `declined`, or whose prompt or end record is missing, is skipped and counted in `skipped`; the `_safe` scrub drops a record whole and counts `dropped`. Held-out stems apply as for `conflict` (stem `triage` is held out like any stem). `--since` filters on the call's `clock.wall_start`. Records sort by the existing `(stem, run_seq, attempt)` key, so repeat exports are byte-identical. `render` does no box I/O.
- compatibility: default `--kinds` is unchanged, so default exports write the same four files; other kinds keep their shape.
- acceptance: criteria 1-4.
- tests: tests/unit/test_training_triage_records.py
- post-merge source of truth: clutch/training.py

### Command surface
- disposition: extend
- owner: clutch/__main__.py (`training export` parser and handler)
- consumers: operators, `tests/unit/test_main_training_group.py`
- observable change: `--kinds` accepts `triage`; when `triage` is requested the handler reads `Box(config.state_dir / BOX_DIR, checkout.fs).messages()` and passes them as `box_messages`; help and examples name the kind.
- compatibility: existing flags, defaults and exit codes are unchanged.
- acceptance: criterion 5.
- tests: tests/unit/test_main_training_group.py
- post-merge source of truth: clutch/__main__.py

## Scope in / Scope out
Scope in:
- `clutch/training.py`: the `triage` kind, `box_messages` keyword, the label rule, the `triage` count, and the `report` line.
- `clutch/__main__.py`: add `triage` to the `--kinds` choices (not the default), read box messages when requested, pass them, and add `triage` to the `export` help text and example.
- `tests/unit/test_training_export.py`: update only the two `training.report(dict(...))` calls so their dict carries `triage=0` (the new count key).
- `tests/unit/test_main_training_group.py`: add `triage` to the accepted-kinds assertions only.
- `clutch/docs/host-running.md` (`training export` row), `docs/how-clutch-works.md` (section 2 `training export` row) and `clutch/docs/host-training.md` (the kinds sentence): add `triage` to the kinds list and one clause that the label is the operator override of the verdict.
- The plan document stays unedited (owner-revised); the `override_report` linkage gap is stated in Goal.

Scope out: a box field linking override_report messages to triaged messages; a `training eval` triage lens (the roadmap row waiting on a label source); panel-member calls keyed with a scoped sequence (`m<index>`), which `_calls` already skips for non-integer `run_seq`; changing default kinds.

## Scope fence
- clutch/training.py
- clutch/__main__.py
- clutch/docs/host-running.md
- clutch/docs/host-training.md
- docs/how-clutch-works.md
- tests/unit/test_training_export.py
- tests/unit/test_main_training_group.py
- tests/unit/test_training_triage_records.py

## Acceptance criteria
1. A triage call with reply verdict `author` whose box message (same seq) is resolved with `Resolution(kind="declined")` yields a `triage` record labelled `negative`; the same call with resolution kind `ticket` is labelled `merged`; with a pending message, or no message of that seq, `neutral`; checked by `./dev.py test tests/unit/test_training_triage_records.py`. A mapping that treats `author` vs `ticket` as a disagreement is ruled out by the `merged` case.
2. The record has `kind == "triage"`, `stem == "triage"`, `run_seq` equal to the message seq, user content equal to the prompt blob and assistant content equal to the reply text; a reply that is not valid JSON or has a verdict outside the three is skipped and counted in `skipped`, not written; checked by `./dev.py test tests/unit/test_training_triage_records.py`.
3. `since="2026-11-10"` drops a call with `wall_start` `2026-11-09T23:59:59Z` and keeps one on `2026-11-10`; a record containing a `Bearer` token of 20 or more characters is counted in `dropped`, not written; `triage.jsonl` is absent from `files` when `triage` is not in `kinds`; checked by `./dev.py test tests/unit/test_training_triage_records.py`.
4. `training.report` prints `triage: N` and two renders of the same sources are byte-identical; checked by `./dev.py test tests/unit/test_training_triage_records.py tests/unit/test_training_export.py`.
5. `--kinds triage` parses to `["triage"]`, the default kinds list is unchanged at four entries without `triage`, and the formatted `training export` help contains `triage`; checked by `./dev.py test tests/unit/test_main_training_group.py`. The three docs naming `triage` in the kinds list is a one-time review check.

## Verification
```
./dev.py test tests/unit/test_training_triage_records.py tests/unit/test_training_export.py tests/unit/test_main_training_group.py tests/unit/test_training_export_kinds.py tests/unit/test_training_export_conflict.py tests/unit/test_training_ticket_kind.py tests/unit/test_main_help.py tests/unit/test_host_running.py
```

## Definition of rejected
The branch adds `triage` to the default kinds, reads the box or any file inside `render`, invents a link between override_report messages and triaged messages, adds a Message field, writes a partly built record, adds tests to a hot test file, or edits a file outside the fence.

## Time budget
- expected: 25m
- stuck: 50m
