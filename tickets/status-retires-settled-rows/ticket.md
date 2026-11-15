---
state: confirmed
source: human
priority: P1
kind: bug
---

## Depends on
- none

## Context
- clutch/status.py
- tests/unit/test_status_verdict_decisions.py
- tests/integration/test_status.py::test_status_preserves_sections_and_is_write_free
- tests/integration/test_cli.py::test_status_projects_the_journal
- tests/integration/test_cli.py::test_status_is_deterministic
- docs/how-clutch-works.md#10.3

## Goal / Why
`clutch status` prints 2052 lines on this repo, and 1500 of them are finished work (`tickets/status-retires-settled-rows/evidence/status-noise.txt`). `project` folds the whole journal into each list and never drops an entry once its ticket is done, so every list grows for the life of the journal: `merged` is 524 stems, `intake` is 939 rows for 518 stems because it keeps one row per intake event, and `blocked` is 42 rows of which 37 are `rejected` or `already_satisfied` -- work nobody is waiting on, under a heading that says they are blocked. `verdict_refusals` and `reopens` fold the same way and are empty here only because nothing has produced one yet. The live state the output exists to show -- `in flight`, the Reject queue, what needs an operator -- is five lines buried in the middle.

`verdict-decisions-retire-on-resolution` fixed this defect for `verdict_decisions` in the same function: `project` walks the events in reverse, tracks which stems have since been resolved, and drops any entry whose ticket is in that set (`clutch/status.py` lines 196-204). The other lists never got the rule. After this change the four journal-folded lists carry only entries whose ticket is neither settled nor rejected, `merged` renders as a count, and `clutch status` on this journal is under 600 lines.

## Scope in / Scope out
Scope in, all in `clutch/status.py`:
- In `project`, after `last = last_states(events)`, bind one local `done = SETTLED | {"rejected"}`, the idiom this module already uses at lines 114, 131 and 141 and `clutch/observe.py` line 311 names the same way.
- Filter the `intake` comprehension with `last.get(e.ticket) not in done`.
- Change the `blocked` comprehension from `if to not in ("merged", "running")` to `if to != "running" and to not in done`. `gate_failed`, `premise_failed`, `infra_error`, `incomplete` and `abandoned` all still appear: they need a reader.
- Filter `verdict_refusals` with `last.get(e.ticket) not in done`.
- Filter `reopens` to a message that is still unresolved: build the id set from the `messages` list already bound in `project` (`m.resolution is None`, the test `_box_admission` uses for the same question) and keep an event only when its `body["box_id"]` is in that set.
- In `render`, replace `block("merged", status.merged)` with the one-line form `f"merged:\n{len(status.merged)}"`, matching the `spend` block above it. `Status.merged` keeps every stem, because `len` needs them and nothing else reads the field.

Also in scope, `docs/how-clutch-works.md` section 10.3 (lines 709-722), which states the contents this change makes false: rewrite item 1 so merged is a count and blocked is the stems whose last state is neither `running` nor settled nor rejected, drop the two sentences saying `already_satisfied` is included and "remains in this state listing", and rewrite item 2 so intake, verdict refusals and reopens carry only stems or messages that are not yet settled, rejected or resolved. Items 3 to 7 and the rest of the file do not change.

Scope out: `Status`'s field types and every other field; `SETTLED` itself and the other `SETTLED | {"rejected"}` call sites, which stay as they are rather than being folded into a new shared constant; the Suggestion Box block, which is the next-largest block at 469 rows but whose resolved rows are the only thing that renders `row`'s `author -> `, `tombstone -> ` and `declined` labels, so hiding them would orphan that code and the test that pins it (`test_box_status_labels_and_summary`); de-duplicating `intake` to one row per stem; adding dates or recency ordering to any list; `clutch/observe.py` and the extension snapshot, which build their own rows and read none of these five fields; `clutch/help.py`, whose `status` topic names the extension's per-ticket row statuses, not the sections of this rendered output; and `clutch/docs/host-running.md`, which describes `status` as "Show the journal projection" without naming a section.

Three tests pin the old output and are rewritten, not deleted:
- `tests/integration/test_cli.py::test_status_projects_the_journal`: the merged assertion becomes the count (`section["merged:"] == "1"`), which still rules out stem `b`, whose last state is `running`.
- `tests/integration/test_cli.py::test_status_is_deterministic` (line 332) merges stems `z`, `a` and `m` and asserts `first.index("- a") < first.index("- m") < first.index("- z")`. With no `- z` line left, `str.index` raises `ValueError`, and the sort order of merged stem names is no longer in the output at all. Keep the two-run byte-equality check and the `"- merged tickets: 3\n"` assertion, and replace the index-order assertion with `"merged:\n3\n" in first`.
- `tests/integration/test_status.py::test_status_preserves_sections_and_is_write_free`: in both `legacy` strings the merged block becomes the count (`1` populated, `0` empty). Stem `held` (`gate_failed`) stays in `blocked` and stem `new` stays in `intake`, having no terminal state, so no other line of either string moves.

## Scope fence
- clutch/status.py
- tests/unit/test_status_retirement.py
- tests/regress_status_retires_settled_rows.py
- tests/integration/test_status.py
- tests/integration/test_cli.py
- docs/how-clutch-works.md

## Acceptance criteria
1. `tests/unit/test_status_retirement.py::test_intake_drops_settled_and_rejected_stems` builds four `ticket_intake` signals, for stems `gone` (later `rejected`), `done` (later `merged`), `same` (later `already_satisfied`) and `live` (no state transition at all), and asserts `[row[0] for row in project(events).intake] == ["live"]`. Ruled out: all four stems, which is today's result, and `[]`, which a filter that requires a non-settled state rather than the absence of a settled one would give.
2. `tests/unit/test_status_retirement.py::test_blocked_keeps_only_states_needing_a_reader` gives one stem each of `gate_failed`, `premise_failed`, `infra_error`, `incomplete`, `abandoned`, `rejected`, `already_satisfied`, `merged` and `running`, and asserts `project(events).blocked` equals exactly the five pairs for `gate_failed`, `premise_failed`, `infra_error`, `incomplete` and `abandoned`, sorted by stem. Ruled out: the `rejected` and `already_satisfied` pairs being present, which is today's result, and `abandoned` being absent, which filtering on `clutch/journal.py`'s `TERMINAL_STATES` instead of `SETTLED | {"rejected"}` would give.
3. `tests/unit/test_status_retirement.py::test_verdict_refusals_drop_settled_and_rejected_stems` journals a `ticket-plane/` effect completion carrying `result.refusal` for a stem later `merged` and another for a stem left at `gate_failed`, and asserts `project(events).verdict_refusals` is the single row for the `gate_failed` stem. Ruled out: both rows, and `()`.
4. `tests/unit/test_status_retirement.py::test_reopens_drop_resolved_messages` passes a `box` holding one unresolved message and one resolved one, journals a `tombstone_auto_reopened` signal naming each `box_id`, and asserts `[body["box_id"] for body in project(events, box=box).reopens]` is the unresolved id alone. Ruled out: both ids, and `[]`.
5. `tests/unit/test_status_retirement.py::test_merged_renders_as_a_count` asserts `render(project(events))` for two merged stems contains `"merged:\n2\n"` and contains neither stem name in that block. Ruled out: the bulleted name list, which is today's result, and a `(none)` or `- 2` form.
6. `./dev.py test tests/integration/test_status.py tests/integration/test_cli.py` exits 0 with the three pinned tests rewritten as `## Scope in / Scope out` describes, so `test_status_preserves_sections_and_is_write_free` still proves `status` takes no lock and writes nothing and `test_status_is_deterministic` still proves two runs print the same bytes.
7. `uv run python tests/regress_status_retires_settled_rows.py` prints `{"regression_result": "pass"}` and exits 0 on the branch head, and `{"regression_result": "defect"}` with a non-zero exit at the merge base. It builds the events in process, with no clock, filesystem or journal read, as `tests/regress_verdict_decisions_retire_on_resolution.py` does.
8. The last `## Verification` command before `./dev.py test` exits 0: `docs/how-clutch-works.md` still has its `### 10.3 ` heading and no longer contains any of the three sentences this change makes false -- `every other state, including`, `remains in this state listing` and `2. Every intake.`. Ruled out: the stale sentences left in place, and a repair that deletes section 10.3 instead of rewriting it.
9. `./dev.py test` exits 0.

## Verification
```
./dev.py test tests/unit/test_status_retirement.py
./dev.py test tests/integration/test_status.py tests/integration/test_cli.py
uv run python tests/regress_status_retires_settled_rows.py
uv run python -c "import pathlib; t = pathlib.Path('docs/how-clutch-works.md').read_text(); assert '### 10.3 ' in t; assert 'every other state, including' not in t; assert 'remains in this state listing' not in t; assert '2. Every intake.' not in t"
./dev.py test
```

## Definition of rejected
The branch is rejected if it drops an entry whose ticket still needs a reader (`gate_failed`, `premise_failed`, `infra_error`, `incomplete`, `abandoned`), if it adds a config knob, a row cap, a time window or a `--verbose` style flag to decide what `status` prints, if it introduces a new module-level constant or helper for `SETTLED | {"rejected"}` and rewrites the existing call sites, if it changes the Suggestion Box block, or if it reaches the same output by trimming inside `render` instead of retiring the entries in `project`.

## Time budget
- expected: 40m
- stuck: 90m

## Regression
```
uv run python tests/regress_status_retires_settled_rows.py
```
- carries: tests/regress_status_retires_settled_rows.py
