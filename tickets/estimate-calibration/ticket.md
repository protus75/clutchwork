---
state: confirmed
source: human
priority: P1
kind: feature
---

## Depends on
none

## Context
- clutch/llmeffect.py::llm_key
- clutch/llmeffect.py::_cost
- clutch/effects.py::Effects.run
- clutch/journal.py::SIGNAL_NAMES
- clutch/stats.py::_summary
- clutch/config.py::Evidence
- clutch/config.py::Config
- clutch/__main__.py::_command
- clutch/__main__.py::_parser
- clutch/__main__.py::main
- clutch/docs/host-running.md
- docs/how-clutch-works.md#2.1 Verbs
- docs/how-clutch-works.md#11. Config
- clutch/docs/host-contract.md#Complete field inventory
- tests/integration/test_closed_sets.py::test_journal_closed_sets_and_constants
- tests/integration/test_host_contract.py::test_host_contract_schema_coverage
- tests/unit/test_host_running.py
- tests/unit/test_release_publish.py::test_main_release_journals_the_release_signal
- tests/fakes.py

## Goal / Why
Roadmap row 142 (`estimate-calibration`, owner request 2026-11-17), part 1 of 3. Decision 22 (`docs/roadmap.md` section 6) makes ticket time budgets AI time: the actual Implement minutes on the model that runs the ticket. On 2026-11-17 actual Implement minutes were about a tenth of the estimates for every model, so `stuck` budgets (twice the estimate) run about 20 times too long and decision 22's 30- and 60-minute limits measure an inflated number. Nothing in clutch measures that today.

The journal already holds every fact the measurement needs except the estimate, so this ticket adds no new recording. Each model call is an Effect keyed `llm/<stem>/<run_seq>/<surface>/<attempt>/<call_seq>` (`clutch/llmeffect.py::llm_key`). `Effects.run` journals an `effect_intent` after provider admission, before the call, and an `effect_completion` when the call returns. The completion's `cost` carries `provider` and `model` (`clutch/llmeffect.py::_cost`). The engine log is a diagnostic log, not the record, so the calculation reads the journal only. The estimate is the `- expected: <N>m` line of `tickets/<stem>/ticket.md`, read as the file is now. On 2026-11-17 that file's estimate matched the estimate that ran for 1,381 of the 1,417 journaled Implement completions whose `running` transition recorded a ticket blob. Reading each run's blob instead would cost one git process per run.

When this ticket is done:
- `clutch engine calibrate` takes the last `calibration.every` (default 100) completed Implement calls from the journal and groups those whose ticket has an estimate by provider and model. For each group it gives the run count, the median estimate, and the median and 90th-percentile actual minutes, measured from each call's intent to its completion. It journals the table as one `estimate_calibration` signal and prints it. On a prototype at `6e6d9154`, run against a copy of this repo's journal on 2026-11-17, it printed `codex/gpt-6.1-sol: 5 runs, estimate p50 60.0m, actual p50 13.2m, actual p90 16.7m` and `codex/gpt-6.1-terra: 95 runs, estimate p50 30.0m, actual p50 4.9m, actual p90 9.8m`, in 0.5 seconds.
- The new config key `calibration.every` sets the window. Its row name is the cadence the owner named. Part 2 (`estimate-calibration-idle`) has drain and serve also run the calibration at their idle point every that many calls. Part 3 (`estimate-calibration-author`) puts the latest table in Author's prompt and points the authoring guide at it. Each later part needs this ticket's merged code.

Why: authors, the Author stage and the chat sessions that write tickets, need a measured table to write estimates in AI minutes. The row asks for the table to be recorded in the journal, which is the record, so Author can read it later.

## Scope in / Scope out
In, new `clutch/calibration.py`. Parts 2 and 3 use these names, so keep them:
- `ESTIMATE_CALIBRATION = "estimate_calibration"`, a module-level string constant. `tests/integration/test_vocabularies.py::test_every_engine_signal_name_is_listed` resolves module constants used as a signal body's `signal` value.
- `implement_runs(events) -> list[tuple[str, str, str, float]]`. It walks events in journal order and considers only those whose `key` fullmatches the Implement shape of `llm_key`, `llm/<stem>/<run_seq>/implement/<attempt>/<call_seq>`, with each part free of `/`. An `effect_intent` records its `ts` for its key. A later intent for the same key replaces the earlier one, because a crash re-executes the call. An `effect_completion` whose key has a recorded intent and whose `body["cost"]` is a dict yields `(stem, cost["provider"], cost["model"], minutes)`. The minutes run from the recorded intent's `ts` to the completion's `ts`.
- `calibrate(journal, fs, repo, every) -> list[dict]`. The window is the last `every` items of `implement_runs(journal.read())`. For each stem in the window, read `repo / ticket_path(stem)` through `fs.read_bytes` (the filesystem seam). The estimate is the integer of the first line matching `^- expected: (\d+)m$`. A stem whose ticket is missing, unreadable (`OSError`, `UnicodeError`) or has no such line leaves its runs out. Group the remaining runs by `(provider, model)`, in sorted order. For each group, a row dict has exactly the keys `provider`, `model`, `runs` (count), `expected_p50`, `actual_p50` and `actual_p90`. Take the percentiles from `clutch.stats._summary`, imported by name, so they match `clutch stats` (linear interpolation, one decimal). Do not write a second percentile helper. Then append one `EventType.SIGNAL` event with no ticket and the body `{"signal": ESTIMATE_CALIBRATION, "window": every, "rows": rows}`, also when `rows` is empty, and return `rows`.
- `render(rows) -> str`. It returns one line per row, `f"{provider}/{model}: {runs} runs, estimate p50 {expected_p50}m, actual p50 {actual_p50}m, actual p90 {actual_p90}m\n"`, or `"none\n"` when there are no rows.

In, other code:
- `clutch/journal.py`: `SIGNAL_NAMES` gains `"estimate_calibration"`.
- `clutch/config.py`: a new `class Calibration(StrictModel)` with `every: Count = 100`, and `Config` gains `calibration: Calibration = Calibration()` after `retro`.
- `clutch/__main__.py`:
  - The `engine` group's `description` becomes `Run tickets, control a running engine, and run retros and estimate calibrations.`.
  - A new `_command(engine_sub, "calibrate", ...)` after `retro`, with no arguments. Summary: `journal actual Implement minutes against ticket estimates`. Does: computes, per provider and model, the run count, the median estimate, and the median and 90th-percentile actual minutes of the last `calibration.every` completed Implement calls, journals them as an `estimate_calibration` signal, and prints the table. Reads: config, the journal, and the tickets of the stems in the window. Writes: one `estimate_calibration` journal signal. Lock: none, because the journal append takes `journal.lock`. Exits: 0 when recorded; 2 on refusal. Example: `clutch engine calibrate`.
  - A handler `handle_calibrate`, dispatched from the `engine` entry of `handlers` as `"calibrate"`. It runs after the config load and checkout build, like `stats`, and prints `render(calibrate(checkout.journal, checkout.fs, repo, config.calibration.every))` with `end=""`, then returns 0. Refusals (bad config, journal corruption) keep going through `main`'s existing `except` and `_fail`.

In, documents. Only these parts change:
- `clutch/docs/host-contract.md`, the `config-fields` block: `Config` defaults gain `calibration: {every: 100}`, and a new `Calibration:` row has `required: []` and `defaults: {every: 100}`. `tests/integration/test_host_contract.py::test_host_contract_schema_coverage` fails without both.
- `clutch/docs/host-running.md`: a new row after `engine retro`: `` | `engine calibrate` | Yes | Journal and print, per provider and model, the median estimate and the median and 90th-percentile actual Implement minutes of the last `calibration.every` completed Implement calls. | ``. `tests/unit/test_host_running.py::test_verb_table_matches_parser` fails without it.
- `docs/how-clutch-works.md`:
  - Section 2.1 gains a row after `engine retro`, with lock `no`. It says: the verb reads the last `calibration.every` completed Implement calls from the journal, each call's minutes from its `effect_intent` to its `effect_completion`, and its provider and model from the completion's `cost`. It reads each call's ticket `expected` minutes from `tickets/<stem>/ticket.md`. It journals one `estimate_calibration` signal whose rows give, per provider and model, the run count, median estimate, and median and 90th-percentile actual minutes, and prints them. Calls whose ticket has no readable estimate are left out.
  - Section 11's table gains a row after `retro`: `` | `calibration` | `every` (default 100): the number of most recent completed Implement calls an `engine calibrate` table covers | ``.

In, tests:
- `tests/integration/test_closed_sets.py::test_journal_closed_sets_and_constants`: add `"estimate_calibration"` to the pinned `SIGNAL_NAMES` set. Nothing else in the file changes.
- New `tests/unit/test_calibration.py` (criteria 1-4). It builds events with `tests.fakes.FakeJournal` and `FakeClock` and tickets with `FakeFileSystem`, and reads no repo file.
- New `tests/unit/test_main_engine_calibrate.py` (criterion 5). It runs `main` in `tmp_path` with `clutch.__main__.load_config` and `child_env` patched, as `tests/unit/test_release_publish.py::test_main_release_journals_the_release_signal` does. It writes a real `Journal` and a ticket only under `tmp_path`.

A scratch prototype of exactly this change on `6e6d9154` touched the 10 fenced files. With it, the full unit suite (919 tests), `ruff check` and `ruff format --check` passed. The unit coverage gate also passed, with `clutch/calibration.py` at 100%; it has no `[coverage.files]` row, so the 90% default applies. The full integration suite passed 3,410 tests, against 3,409 without the change: `test_closed_sets.py` has one parametrized case per signal name.

Merge order. `cli-group-provider` (row 136, confirmed and running) also fences `clutch/__main__.py`, `clutch/docs/host-running.md`, `clutch/docs/host-contract.md` and `docs/how-clutch-works.md`. It edits the `install` and `probe` parsers, the pre- and post-config sets, their `handlers` entries, their run-guide and section 2.1 rows, and host-contract's Install, Onboarding and setup prose. This ticket edits the `engine` group, its handler dict, the rows after `engine retro`, section 11's table and the `config-fields` block. No changed line is shared or adjacent, and each criterion holds in either order. Only the top-level `clutch help` listing gains `provider ...` lines. `evidence-record-doc-section` (confirmed) inserts a section 10.4 before `## 11. Config`. This ticket's section 11 row sits in the table below that heading, so either order merges.

Out:
- The idle-point cadence in `clutch/drain.py` and `clutch/serve.py` (part 2, `estimate-calibration-idle`), and Author's prompt, `clutch/author.py`, `clutch/specs/author.md` and the authoring guide (part 3, `estimate-calibration-author`).
- Changing `stuck` or `expected` on any ticket, lint's time budget rules, and `drain.max_ticket_minutes`.
- Reading `engine.log`, `run.md`, the evidence store, or each run's ticket blob through git.
- Killed or timed-out Implement calls, which journal no completion and so no model. On 2026-11-17 this repo's journal held 29 such Implement intents against 1,444 completions.
- A command option (window, provider filter, `--json`), a writer lock, and a control request to a running engine.
- `README.md`, which lists a subset of commands without `engine retro`; `clutch/help.py`, `clutch/observe.py` and `vscode-clutchwork/` (no extension surface shows the verb); and `config.yaml`, which keeps the default.

## Scope fence
- clutch/calibration.py
- clutch/journal.py
- clutch/config.py
- clutch/__main__.py
- clutch/docs/host-contract.md
- clutch/docs/host-running.md
- docs/how-clutch-works.md
- tests/integration/test_closed_sets.py
- tests/unit/test_calibration.py
- tests/unit/test_main_engine_calibrate.py

## Acceptance criteria
1. `tests/unit/test_calibration.py::test_implement_runs_pair_each_completion_with_its_latest_intent` journals, with a `FakeClock` advanced between events, in this order: an Implement call for stem `a` that takes 6 minutes (`codex`/`m1`); a `review` call for `a` that takes 2 minutes; an intent for `b`, 10 minutes, then a second intent and completion for the same key 3 minutes apart (`claude`/`m2`); and an Implement completion for `c` with no intent. `implement_runs` returns exactly `[("a", "codex", "m1", 6.0), ("b", "claude", "m2", 3.0)]`. Ruled out: counting the review call or the intentless completion, and timing the re-executed call from its first intent (13.0).
2. `tests/unit/test_calibration.py::test_calibrate_journals_one_row_per_provider_and_model` has tickets `a` (30m), `b` (60m) and `c` (20m), a ticket `d` with no `- expected:` line, and no ticket for `gone`. It journals, in order, Implement calls `old` 50 minutes, `a` 3 (`codex`/`m1`), `b` 9 (`codex`/`m1`), `c` 2 (`claude`/`m2`), `d` 1 and `gone` 1. `calibrate(journal, fs, repo, 5)` returns exactly `[{"provider": "claude", "model": "m2", "runs": 1, "expected_p50": 20.0, "actual_p50": 2.0, "actual_p90": 2.0}, {"provider": "codex", "model": "m1", "runs": 2, "expected_p50": 45.0, "actual_p50": 6.0, "actual_p90": 8.4}]`. The journal then holds exactly one signal, with no ticket and body `{"signal": "estimate_calibration", "window": 5, "rows": <those rows>}`. Ruled out: including `old` (outside the last 5), `d` or `gone`; pooling the two models; a p90 that is not interpolated (9.0); and printing without journaling.
3. `tests/unit/test_calibration.py::test_calibrate_journals_an_empty_table`: on an empty journal, `calibrate(..., 100)` returns `[]` and journals exactly `{"signal": "estimate_calibration", "window": 100, "rows": []}`. Ruled out: an exception or no record when no run has an estimate.
4. `tests/unit/test_calibration.py::test_render`: the criterion-2 `codex` row renders as `codex/m1: 2 runs, estimate p50 45.0m, actual p50 6.0m, actual p90 8.4m\n`, and `render([])` is `none\n`. Ruled out: an empty string for no rows.
5. `tests/unit/test_main_engine_calibrate.py`:
   - `test_calibrate_is_an_engine_subcommand`: `["engine", "calibrate"]` parses to `engine_verb == "calibrate"`; `calibrate` is not a top-level choice; and `["calibrate"]` and `["engine", "calibrate", "extra"]` raise `SystemExit(2)`.
   - `test_main_calibrate_journals_and_prints`: a `tmp_path` journal holds one 4-minute Implement call for `a` (`codex`/`m1`), `tickets/a/ticket.md` says `- expected: 30m`, the patched config has `calibration=Calibration(every=7)`, and `clutch.__main__.Lockfile` is replaced by a function that raises. `main(["engine", "calibrate"], cwd=tmp_path, env={}, clock=...)` returns 0, prints exactly `codex/m1: 1 runs, estimate p50 30.0m, actual p50 4.0m, actual p90 4.0m\n`, and the journal's last event body is `{"signal": "estimate_calibration", "window": 7, "rows": [...]}` with that row.
   - Ruled out: a top-level `calibrate`, an option, taking the writer lock, a window that ignores `calibration.every`, and a print without a journal record.
6. `./dev.py test tests/unit/test_main_help.py tests/unit/test_host_running.py tests/unit/test_evidence_config.py` exits 0 with those files unchanged. `uv run clutch help engine calibrate` prints `usage: clutch engine calibrate`, the does text, then `Reads:`, `Writes:`, `Lock:` and `Exit codes:` lines that agree with Scope in, then `Examples:` with a `clutch engine calibrate` line. `uv run clutch help engine` lists `calibrate` and its summary.
7. `./dev.py test tests/integration/test_closed_sets.py tests/integration/test_vocabularies.py tests/integration/test_host_contract.py tests/integration/test_config.py` exits 0. In `test_closed_sets.py` only the pinned `SIGNAL_NAMES` set gains `"estimate_calibration"`. The other three files are unchanged, and `test_every_engine_signal_name_is_listed` finds the new name emitted from `clutch/calibration.py`.
8. `grep -c '^| .engine calibrate. |' clutch/docs/host-running.md docs/how-clutch-works.md` prints `1` for each file, `grep -c '^| .calibration. | .every. (default 100)' docs/how-clutch-works.md` prints `1`, and `grep -c 'calibration: {every: 100}' clutch/docs/host-contract.md` prints `1`.
9. `./dev.py test` exits 0. Check's `unit` (with the coverage gate) and `integration` mechanical checks in `config.yaml` run both full suites.

## Verification
```
./dev.py test tests/unit/test_calibration.py tests/unit/test_main_engine_calibrate.py tests/unit/test_main_help.py tests/unit/test_host_running.py tests/unit/test_evidence_config.py
./dev.py test tests/integration/test_closed_sets.py tests/integration/test_vocabularies.py tests/integration/test_host_contract.py tests/integration/test_config.py
```

## Definition of rejected
The branch is rejected, even if it passes, when:
- The calculation reads `engine.log`, `run.md` or the evidence store, calls git, or counts a call surface other than `implement`.
- `engine calibrate` takes the writer lock, submits a control request, takes an option, or prints a table it did not journal.
- A second percentile helper is written instead of reusing `clutch.stats._summary`.
- Drain, serve, Author, the authoring guide, a ticket's time budget, or lint's budget rules change (parts 2 and 3 own the first four).
- A file outside the fence changes, or an existing assertion is dropped or loosened.

## Time budget
- expected: 20m
- stuck: 40m
