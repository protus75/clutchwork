---
state: draft
source: human
priority: P0
kind: feature
---

## Depends on
none

## Context
- clutch/observe.py::read_lines
- clutch/observe.py::journal
- clutch/observe.py::as_events
- clutch/observe.py::recent_steps
- clutch/observe.py::lock_holder
- clutch/status.py::SETTLED
- clutch/status.py::RETIRED
- clutch/status.py::CLOSED
- clutch/status.py::reject_queue
- tests/unit/test_main_view_group.py
- tests/unit/test_host_running.py
- tests/unit/test_readme.py
- tests/integration/test_ask_drain_loop_agent.py

## On-demand
- clutch/__main__.py
- clutch/specs/ask/plan-ticket-drain.md
- clutch/specs/ask/drain-loop.md
- clutch/docs/host-running.md
- docs/how-clutch-works.md
- README.md

## Goal / Why
Roadmap row 161, owner request 2026-11-19. A supervising agent (the `clutch prompt plan-ticket-drain` operator and the `clutch prompt drain-loop` loop) today watches this checkout's engine with hand-written watcher scripts, which wake it on every journal write or on a timer. After this ticket a new read-only verb `clutch view events` runs until Ctrl-C and prints exactly one line per actionable engine change in this checkout, and nothing for a poll where nothing actionable changed or for a human-authored draft. Each line names the event, its stem (or `-`), and the clutch verb that acts on it. The filter lives in the new module `clutch/events.py` and is covered by pytest, built on the existing journal and engine-log projections (`observe.journal`, `observe.as_events`, `observe.read_lines`, `observe.recent_steps`, `status.reject_queue`, `status.CLOSED`), so no shell script holds engine policy. Both supervising prompts tell the operator to run `clutch view events` under its agent's monitor facility and act on each line, so supervision wakes only for events it acts on.

## Boundary contract
### `clutch view events` verb and its event lines
- disposition: create
- owner: clutch/events.py (filter, line format, poll loop) and clutch/__main__.py (parser entry and handler)
- consumers: the operator of `clutch/specs/ask/plan-ticket-drain.md` and the loop of `clutch/specs/ask/drain-loop.md`, run under an agent's monitor facility; a person in a terminal
- observable change: new subcommand `clutch view events` with no options. It reads only `<state_dir>/journal/*.jsonl`, `<state_dir>/engine.log` (when it exists) and `<state_dir>/clutch.lock` (through `observe.recent_steps`); it writes nothing, takes no lock and runs no git or process. Every `events.POLL_SECONDS` (5) it polls; the first poll is a silent baseline. Each later poll prints, flushed, one line per change since the previous poll, in this order: journal-derived lines in journal order, then Reject-queue lines sorted by stem, then engine lines in log order. Line format: `<event> <stem or -> [<detail>] -- clutch <verb>`. Closed event vocabulary `events.EVENTS`, each with its fixed acting verb: `start` (a `state_transition` to `running`; `-- clutch roadmap status`); `settle` (a `state_transition` whose `to` is in `status.CLOSED`, detail the state; `-- clutch roadmap status`); `reject_queue` (a stem newly in `status.reject_queue`, detail its `to`; `-- clutch prompt diagnose <stem>`); `reject_release` (a stem that left `status.reject_queue`; `-- clutch view status`); `draft` (a `ticket_intake` signal with `state: draft` and a `source` starting `box:`, detail the source; `-- clutch prompt drafts`); `gate` (a `roadmap_gate` signal, stem `-`, detail `<release> passed|failed`; `-- clutch roadmap status`); `release` (a `release` signal, stem `-`, detail its tag; `-- clutch roadmap status`); `engine_start` (an `observe.recent_steps` row of kind `engine_start`, stem `-`, detail the row text; `-- clutch view status`); `engine_stop` and `engine_lost` (rows of those kinds, stem `-`, detail the row text; `-- clutch prompt drain-loop`). An engine row is printed once, keyed by its kind and `ts`. Every other journal record (effect intents and completions, provider outcomes, non-closed and unrouted terminals, human or seed intake) prints nothing. If the journal holds fewer records than at the previous poll, the poll re-baselines silently. Ctrl-C ends the verb with exit 0; a missing or invalid config refuses with exit 2 as the other `view` verbs do.
- compatibility: additive; no existing verb, journal record, engine-log record or projection changes. `observe` and `status` functions are imported, never edited.
- acceptance: acceptance criteria 1-6
- tests: tests/unit/test_view_events.py, tests/unit/test_main_view_events.py
- post-merge source of truth: clutch/events.py
- closest existing: `clutch view watch` and `observe.text_snapshot` reprint the whole state every three seconds and cannot say what changed; `clutch view status` (`status.project`) prints one full projection and exits; `observe.recent_steps` lists stage and engine rows but no settles, drafts, Reject-queue membership or gate results, and is reused here for the engine rows. None emits deltas.
- earning reason: a new process boundary (a CLI verb) owned by the owner's roadmap row 161, with two production consumers (the two shipped supervising prompts) that today depend on hand-written watcher scripts.

### Supervising prompts
- disposition: extend
- owner: clutch/specs/ask/plan-ticket-drain.md and clutch/specs/ask/drain-loop.md
- consumers: agents running `clutch prompt plan-ticket-drain` and `clutch prompt drain-loop`
- observable change: plan-ticket-drain's Supervising bullet that today says to watch engine state "with your agent's monitor or wait facility" says instead to run `clutch view events` under the agent's monitor facility and act on each line it prints, falling back to a timed check only when no line arrives. drain-loop's step 1 adds that between ticks the loop runs `clutch view events` under its monitor facility and starts the next tick on each line it prints.
- compatibility: every phrase that `tests/integration/test_ask_plan_drain.py`, `tests/integration/test_ask_drain_loop.py`, `tests/integration/test_ask_drain_loop_agent.py`, `tests/unit/test_ask_plan_drain.py` and `tests/unit/test_ask_drain_loop.py` assert present stays present, and every phrase they assert absent stays absent; plan-ticket-drain still does not start with `/loop` and drain-loop still does.
- acceptance: acceptance criterion 7
- tests: tests/integration/test_ask_view_events.py
- post-merge source of truth: the two prompt specs

### Verb documentation
- disposition: extend
- owner: clutch/docs/host-running.md, docs/how-clutch-works.md, README.md
- consumers: host operators and readers of the verb tables; `tests/unit/test_host_running.py` (requires a `view events` row once the parser has the subcommand) and `clutch/help.py` (reads only the rows it names, none of which change)
- observable change: host-running.md gains a `| \`view events\` | Yes | ... |` row after `view stats`; how-clutch-works.md section 2.1 gains a `| \`view events\` | no | ... |` row after `view stats`; README's `# Observing` block gains `uv run clutch view events   # print one line per actionable engine change`.
- compatibility: no existing row changes
- acceptance: acceptance criteria 6 and 8
- tests: tests/unit/test_host_running.py, tests/integration/test_ask_view_events.py
- post-merge source of truth: the parser help in clutch/__main__.py

## Scope in / Scope out
Scope in:
- New `clutch/events.py`, holding `POLL_SECONDS = 5`, the closed vocabulary `EVENTS` (a tuple of the ten event names in the Boundary contract, in that order), a pure `changes(seen, events, log, state)` that takes the previous poll's seen-state (or `None` for the baseline), the journal dicts, the engine-log dicts and the state directory and returns the new seen-state and the lines, a `poll(state, seen)` that reads `observe.journal(state)` and `observe.read_lines(state / "engine.log", 4000)` (empty list when the file is missing) and calls `changes`, and `stream(state, *, sleep, write, interval=POLL_SECONDS)` that loops poll, write each line, `sleep(interval)` forever. The seen-state holds the journal record count, the `status.reject_queue` stem set over `observe.as_events(events)`, and the set of emitted engine-row keys. Engine rows come from `observe.recent_steps(state, log, len(log))`. No new state derivation beyond that classification.
- `clutch/__main__.py`: add the `events` subparser to the `view` group with `_command` (summary, does, reads, writes `Nothing.`, lock `None; works while an engine holds the writer lock.`, exits `0 when stopped by Ctrl-C; 2 on refusal.`, example `clutch view events`); a `handle_events` in the Projections handlers that calls `events.stream(config.state_dir, sleep=time.sleep, write=lambda line: print(line, flush=True))` and returns 0 on `KeyboardInterrupt`; and `"events": handle_events` in the `view` handler table. Nothing else in `__main__.py` changes.
- `clutch/specs/ask/plan-ticket-drain.md` and `clutch/specs/ask/drain-loop.md`: only the edits the Boundary contract names.
- `clutch/docs/host-running.md` (verb table row), `docs/how-clutch-works.md` (section 2.1 verb table row) and `README.md` (`# Observing` block line): only the additions the Boundary contract names.
- New tests in new files: `tests/unit/test_view_events.py`, `tests/unit/test_main_view_events.py`, `tests/integration/test_ask_view_events.py`.

Scope out:
- The VS Code extension, `clutch/help.py` and the snapshot: no extension surface or help topic is added.
- Editing `clutch/observe.py`, `clutch/status.py` or the journal; caching or incremental reads (the full journal is re-read each poll; `journal-duckdb-cache` may speed this later).
- Events beyond the closed vocabulary (stage starts and ends, unrouted `premise_failed`, `gate_failed`, `incomplete`, `infra_error` or `abandoned` terminals, Suggestion Box messages).
- `--once`, JSON output, filters or a configurable interval.
- Existing tests: `tests/unit/test_main_view_group.py`, `tests/unit/test_main_help.py`, `tests/unit/test_host_running.py` and the ask prompt tests pass unchanged; `test_main_help.py` and `test_host_running.py` walk the parser and check the new subcommand automatically.

Merge order with confirmed or drafted unmerged tickets fencing the same files: `snapshot-merged-history-cap` and `snapshot-from-duckdb-cache` edit the `view snapshot` `_command` and the `view snapshot` rows in host-running.md and how-clutch-works.md; `box-issue-process-gap-class` edits README's `box issue` line and host-running.md's upstream-report section; `admission-facts-precomputed` keeps `reject_queue` and `last_states` signatures; `graphics-kind`, `ticket-frontmatter-tolerant-reader` and others edit other parts of `__main__.py` and how-clutch-works.md. This ticket only adds a new subparser, handler, table entry and rows next to `view stats`, so either merge order leaves both changes intact.

## Scope fence
- clutch/events.py
- clutch/__main__.py
- clutch/specs/ask/plan-ticket-drain.md
- clutch/specs/ask/drain-loop.md
- clutch/docs/host-running.md
- docs/how-clutch-works.md
- README.md
- tests/unit/test_view_events.py
- tests/unit/test_main_view_events.py
- tests/integration/test_ask_view_events.py

## Acceptance criteria
1. `tests/unit/test_view_events.py`: with journal segments and an `engine.log` written under `tmp_path`, the baseline `changes(None, ...)` returns no lines even when the history holds merges, drafts and engine rows (a first poll that replays history fails), and a second call with identical inputs returns no lines (a poll that reprints unchanged state fails).
2. `tests/unit/test_view_events.py`: appending, after the baseline, a `running` transition, a `merged` transition, a routed `premise_failed` transition with `routed: reject_queue`, a `reject_verdict` for that stem, a `ticket_intake` with `source: box:roadmap_row, state: draft`, a `roadmap_gate` with `passed: false`, and a `release` signal yields exactly the lines `start <a> -- clutch roadmap status`, `settle <a> merged -- clutch roadmap status`, `reject_queue <b> premise_failed -- clutch prompt diagnose <b>`, `reject_release <b> -- clutch view status`, `draft <c> box:roadmap_row -- clutch prompt drafts`, `gate - <release> failed -- clutch roadmap status` and `release - <tag> -- clutch roadmap status` across the polls that see them, each once, in the order the Boundary contract states; a filter that drops any of them or prints any twice fails.
3. `tests/unit/test_view_events.py`: appending a `ticket_intake` with `source: human, state: draft`, effect intents and completions, a `provider_call_outcome` signal and an unrouted `premise_failed` transition yields no line (a filter that passes human drafts or noise fails); `EVENTS` equals the ten names in Boundary-contract order.
4. `tests/unit/test_view_events.py`: with `tmp_path/clutch.lock` naming the test's own pid and a `started_at` (so `observe.lock_holder` sees a live holder whose pid matches), appending an `engine_start` record with that pid to `engine.log` yields one `engine_start - ... -- clutch view status` line and no `engine_lost` line, and appending an `engine_stop` then yields one `engine_stop - ... -- clutch prompt drain-loop` line; later polls repeat neither. With a second `engine_start` and the lockfile removed (no stop record), one `engine_lost - ... -- clutch prompt drain-loop` line appears, once. A journal shorter than the seen count re-baselines with no lines.
5. `tests/unit/test_view_events.py`: `stream` with a fake `sleep` that appends a merged transition on its first call and raises `KeyboardInterrupt` on its second writes exactly one `settle` line through `write` and calls `sleep` with `POLL_SECONDS`; a loop that calls the real clock or never sleeps fails.
6. `tests/unit/test_main_view_events.py`: `_parser().parse_args(["view", "events"]).view_verb == "events"`, `["view", "events", "--once"]` exits 2, and `main(["view", "events"], ...)` with `events.stream` monkeypatched to raise `KeyboardInterrupt` returns 0 with empty stderr; `./dev.py test tests/unit/test_main_help.py tests/unit/test_host_running.py tests/unit/test_readme.py tests/unit/test_main_view_group.py` exits 0 unchanged, so the help, examples and host-running row exist.
7. `tests/integration/test_ask_view_events.py`: `ask.render("plan-ticket-drain", ...)` and `ask.render("drain-loop", ...)` with a real config each contain `clutch view events` and `monitor facility`, and `./dev.py test tests/integration/test_ask_plan_drain.py tests/integration/test_ask_drain_loop.py tests/integration/test_ask_drain_loop_agent.py tests/unit/test_ask_plan_drain.py tests/unit/test_ask_drain_loop.py` exits 0 unchanged.
8. `tests/integration/test_ask_view_events.py`: `docs/how-clutch-works.md` has a line starting `| \`view events\` |` and `README.md` contains `uv run clutch view events`.

## Verification
```
./dev.py test tests/unit/test_view_events.py tests/unit/test_main_view_events.py tests/integration/test_ask_view_events.py tests/unit/test_main_help.py tests/unit/test_host_running.py tests/unit/test_readme.py tests/unit/test_main_view_group.py tests/integration/test_ask_plan_drain.py tests/integration/test_ask_drain_loop.py tests/integration/test_ask_drain_loop_agent.py tests/unit/test_ask_plan_drain.py tests/unit/test_ask_drain_loop.py
```

## Definition of rejected
- The filter or its event vocabulary lives anywhere but `clutch/events.py`, or a shell script or the extension does any of it.
- `clutch view events` writes a file, takes a lock, or runs git or a process.
- A poll with no actionable change, or a human-source draft, prints a line.
- `clutch/observe.py`, `clutch/status.py`, an existing test file, or the extension is edited.

## Time budget
- expected: 25m
- stuck: 50m
