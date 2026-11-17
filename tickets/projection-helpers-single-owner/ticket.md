---
state: draft
source: human
priority: P1
kind: chore
---

## Depends on
none

## Context
- docs/roadmap.md#2.3 Repeated helpers and projections
- clutch/status.py::last_states
- clutch/journal.py::run_seq
- clutch/enginelog.py
- clutch/observe.py::queue
- clutch/observe.py::text_snapshot
- tests/unit/test_phase_events.py::install_log

## Goal / Why
Roadmap row 125 (`docs/roadmap.md` §2.3 and §2.1 item 10, recurred in 0.3.0). At HEAD (`384cc161`, after `cli-help-standard` merged) five of the row's duplicates are still written out at several call sites:

- Last-state fold. `status.last_states` owns the stem-to-state map, but `observe.text_snapshot`, `observe.snapshot` and `handle_prompt` in `__main__.main` each fold journal dicts into `{stem: {**body, "ts": ts}}` by hand. `provider_holds` in `__main__.build_daemon_core` folds `{stem: body}` by hand. `observe` wraps journal dicts in `SimpleNamespace` four times (twice in `queue`, once each in `text_snapshot` and `snapshot`) to call Event-typed helpers.
- Spend sum. `status.project`, `stats.project_stats` and `retro.measurements` each sum `cost["usd"]` over effect completions.
- `BOX_DIR`. Six joins spell `/ "box"` instead: `__main__.build_control`, `handle_suggest` in `__main__.main`, `ask.render` (two), the evidence copy in `clutch/author.py`, and the box rows in `observe.snapshot`.
- `ticket_path()`. Thirteen sites outside `clutch/tickets.py` spell `tickets/<stem>/ticket.md` themselves: `clutch/__main__.py` (one), `clutch/acceptance.py` (one), `clutch/author.py` (one), `clutch/observe.py` (four), `clutch/retro.py` (one), `clutch/roadmap.py` (three) and `clutch/triage.py` (two).
- `EngineLog` construction. Eight sites build `EngineLog(<config>.state_dir / "engine.log", Redactor.from_config(<config>, <env>), <clock>)`: `clutch/drain.py` (four), `clutch/runner.py` (two), `clutch/serve.py` and `clutch/triage.py`.

After this change each has one owner: `status.latest_transitions` (with `observe.as_events` and `observe.last_bodies` for the watch and snapshot readers), `journal.total_spend`, `box.BOX_DIR`, `tickets.ticket_path` and `enginelog.engine_log`. Every verb's output, the `clutch watch` text and the extension snapshot stay the same. A source scan fails on a new copy. Why: each copy is a place that a later change (a new transition field, a cost field, a moved state directory, the engine-log path) has to find by hand, and the dedup work before parallel runs (0.4.0) assumes one owner.

Already single-owned at HEAD, so dropped: the `providers.py` drought-park lookup and the `observe.ticket_menu_inputs` fold that the roadmap's line numbers point at. Merged `journal-last-transition-helper` moved them onto `journal.last_transition` and `status.last_states`.

Left out of this ticket; each needs its own roadmap row:
1. Attempt counting. The three sites count different things. `caps.failed_attempts` counts failed terminals since the last operator or supervisor keep (the attempts cap). `observe.text_snapshot` shows every non-`running` terminal plus one, drought parks and operator verdicts included. `stats.project_stats` counts `running` transitions. One owner has to choose which number `clutch watch` and `clutch stats` show (for example `journal.run_seq`, which skips drought parks), and that changes displayed values. It is an owner decision, not a move.
2. Frontmatter reads. `observe.frontmatter` and `observe.depends` read tickets by regex because they must also read tickets that fail validation (invalid blocked rows). `retro.production_evidence` reads `expected` from ticket text at old merge commits that current rules may reject. `observe.frontmatter` also reads prompt-spec frontmatter (`clutch/specs/requisition_review.md`, on the engine-plane safety inventory). `__main__._stats` splits with `tickets.split_frontmatter` but loads the YAML itself. One owner needs a new tolerant reader in `clutch/tickets.py`, and its behavior on malformed text is a design choice.
3. The `EngineLog` in `Driver.from_config`. It shares one redactor with the driver's spool. Routing it through `engine_log` adds a second `Redactor.from_config` call, and `tests/integration/test_daemon_composition.py`, a do-not-grow file, pins exactly one after `driver` in its trace.
4. `storm_producer` construction. §2.1 item 10 names it beside `EngineLog`, but row 125 does not.

## Scope in / Scope out
In:
- `clutch/status.py`: add `latest_transitions(events) -> dict[str, Event]`, each stem's latest `state_transition` event whose body has `to`, skipping events whose `ticket` is `None`. `last_states` returns `{stem: e.body["to"] for stem, e in latest_transitions(events).items()}`, the same map as today.
- `clutch/observe.py`:
  - Add `as_events(events: list[dict]) -> list[SimpleNamespace]`, the one wrap of journal dicts. Each object has `type`, `body` (`{}` when absent), `ticket`, `ts` and `key` (each `None` when absent). `queue` calls it once and passes the list to both `operator_holds` and `settled_dependencies`, so its second `SimpleNamespace` generator goes. `text_snapshot` and `snapshot` call it once each. `queue`'s signature is unchanged, because `tests/integration/test_watch.py` calls it with journal dicts.
  - Add `last_bodies(history) -> dict[str, dict]`, returning `{stem: {**e.body, "ts": e.ts}}` built from `status.latest_transitions(history)`. `text_snapshot` and `snapshot` use it in place of their loops. The maps keep their shape, so `running_stems`, `queue` and the row builders are unchanged.
  - Use `BOX_DIR` for the box in `snapshot`. Use `ticket_path` for the box-row resolution link (`ticket_path(m.resolution.link)`), the paths in `capability` and in `snapshot`'s `base` (`ctx.root / ticket_path(stem)`), and the row `path` field (`ticket_path(stem)`).
- `clutch/__main__.py`: `handle_prompt` builds `last` with `observe.last_bodies(observe.as_events(observe.journal(config.state_dir)))`. `provider_holds` iterates `latest_transitions(checkout.journal.read())` and reads each event's `body`. In `build_control`, the `root=` argument of the `storm_producer(...)` call becomes `checkout.config.state_dir / BOX_DIR`, and nothing else in that call changes. `handle_suggest` uses `BOX_DIR` for its `Box`. The `ticket_sha` lambda in `build_daemon_core` uses `f"HEAD:{ticket_path(stem)}"`. Nothing else in this file changes.
- `clutch/journal.py`: add `total_spend(events) -> float` beside `run_seq`. It returns `sum(e.body["cost"].get("usd", 0.0) for e in events if e.type == EventType.EFFECT_COMPLETION and isinstance(e.body.get("cost"), dict))`, the expression `status.project` uses today. `status.project` calls it. `stats.project_stats` sets `usd = total_spend(selected)`; its `costs` list stays for the per-surface and token sums. `retro.measurements` sets `"usd": total_spend(calls)`. Its de-duplicated `llm/` completions stay its own selection, and `costs` stays for the token counts. Every cost body in this repo's journal is a dict carrying `usd` (5,149 of 5,149), so retro's total is unchanged.
- `clutch/enginelog.py`: add `engine_log(config, env, clock) -> EngineLog`, returning `EngineLog(config.state_dir / "engine.log", Redactor.from_config(config, env), clock)`. The eight sites call `engine_log(<checkout>.config, <checkout>.env, <checkout>.clock)`: `clutch/drain.py` (`drain`, `apply` in `settle_admissions`, `_Drain._run_driver`, `_Drain._run_retro`), `clutch/runner.py` (`prepare_pipeline`, `run_ticket`), `clutch/serve.py` (`Serve.__init__`) and `clutch/triage.py` (`report_intake`). Each module imports the name into its own namespace so a test can patch `<module>.engine_log`; `triage.py` keeps its import inside `report_intake`. Each site still makes exactly one `Redactor.from_config` call with the same config object, so the `redactor` trace in `tests/integration/test_daemon_composition.py` is unchanged.
- `BOX_DIR` in `ask.render` (both joins) and in the evidence copy in `clutch/author.py` (`bounded(... / BOX_DIR, ...)`).
- `ticket_path` in `clutch/acceptance.py` (the row-state check), `author.is_rejected`, `retro.production_evidence` (`f"{row['commit']}:{ticket_path(row['ticket'])}"`; its `expected` regex stays), `clutch/roadmap.py` (the two `in files` checks and `draft_stems`) and `clutch/triage.py` (the authored-commit read as `f"{commit}:{ticket_path(stem)}"`, and the tombstone `committed` check as `Path(ticket_path(reply.link))`).
- Remove each import an edit leaves unused, such as `EngineLog` and `Redactor` in `clutch/drain.py`, `clutch/runner.py` and `clutch/serve.py`. `uv run ruff check .` is a hard gate.
- `tests/unit/test_phase_events.py`: `install_log` patches `module.engine_log` with `lambda *args: log` in place of its `EngineLog` and `Redactor.from_config` patches, because `runner` and `drain` no longer bind either name. `tests/unit/test_verdict_extension.py::test_drain_logs_refusal`: the same swap for `drain`. No assertion in either file changes.
- New `tests/unit/test_projection_helpers_single_owner.py`: in-memory events and `tmp_path` only, no repo file and no process. It runs every line this ticket adds to a file with a coverage floor (`latest_transitions`, `as_events`, `last_bodies`, `total_spend`, `engine_log`). Every other edit replaces an existing line or import.
- New `tests/integration/test_projection_helpers_source.py`: it reads `clutch/**/*.py` with `ast`, in the style of `tests/integration/test_scan_owners.py`.

Out:
- The four left-out items in Goal / Why. `clutch/driver.py`, `clutch/caps.py` and `clutch/tickets.py` are not edited. No `storm_producer(...)` call is moved, merged or given a new owner; the only edit to one is the `root=` argument in `build_control` named in Scope in.
- In `clutch/observe.py`: the attempt count in `text_snapshot`, the `frontmatter` and `depends` readers, the `"engine.log"` reads and the watch globs (`tickets/*/ticket.md`, `box/*.json`).
- Glob patterns such as `(repo / "tickets").glob("*/ticket.md")`, and paths to other files under `tickets/<stem>/` (`run.md`, `attempts/`, `evidence/`, `rework.md`).
- `status.reject_queue` and `stats._latest_settled`. They are filtered folds, not the last-state map.
- No docs change. No document names these helpers, and no output changes.
- No signature change to `queue` or `running_stems`, and no edit to a do-not-grow test file.

Behavior note: `status.latest_transitions` skips a `state_transition` without `to`, as `last_states` does today. The hand folds in `observe` and `__main__` did not skip it. This repo's journal holds no such event (0 of 3,100 transitions, none with an empty `ticket`), and every writer sets `to`.

Merge order. `cli-help-standard` merged at `e09d9e05`; it left `build_control`, `build_daemon_core`, `handle_prompt` and `handle_suggest` in `clutch/__main__.py` as they were, and every count above was re-checked after it. No confirmed, unmerged ticket fences a file in this fence. The running `engine-callerless-code` deletes symbols in `clutch/effects.py`, `clutch/heartbeat.py`, `clutch/timers.py`, `clutch/git.py`, `clutch/requisition.py` and `clutch/watchdog.py`, none of which the source scan flags, and its new unit tests patch neither `EngineLog` nor `engine_log`. Confirmed `rule-restatements-single-home` edits only documents and `tests/integration/test_unit_io_rule.py`. So either merge order leaves both suites green.

## Scope fence
- clutch/status.py
- clutch/journal.py
- clutch/observe.py
- clutch/__main__.py
- clutch/stats.py
- clutch/retro.py
- clutch/enginelog.py
- clutch/drain.py
- clutch/runner.py
- clutch/serve.py
- clutch/triage.py
- clutch/ask.py
- clutch/author.py
- clutch/acceptance.py
- clutch/roadmap.py
- tests/unit/test_phase_events.py
- tests/unit/test_verdict_extension.py
- tests/unit/test_projection_helpers_single_owner.py
- tests/integration/test_projection_helpers_source.py

## Acceptance criteria
1. `tests/unit/test_projection_helpers_single_owner.py` builds `journal.Event` objects in memory. Stem `a` has `running`, `gate_failed`, `running`; stem `b` interleaves with it; stem `c` has only a `signal`; one transition has `ticket=None`; stem `d` has `merged` followed by a transition whose body has no `to`. `status.latest_transitions(events)["a"]` is the last `running` event object, not the first and not the `gate_failed` one. `"d"` maps to the `merged` event, not the `to`-less one. Neither `"c"` nor `None` is a key. `status.last_states(events)` equals `{"a": "running", "b": <b's last state>, "d": "merged"}`. Checked by `./dev.py test tests/unit/test_projection_helpers_single_owner.py`.
2. The same file runs `observe.as_events` over a dict with all five fields and a dict with only `type`, `ticket` and `ts`. Each object's `type`, `ticket`, `ts`, `key` and `body` match the dict, and the second has `body == {}` and `key is None`, not an `AttributeError`. For stem `a` journaled `running` at `t1`, then `merged` with `commit: c1` at `t2`, `observe.last_bodies(observe.as_events(dicts))` returns `{"a": {"to": "merged", "commit": "c1", "ts": t2}}`, not the `running` body and not a body without `ts`.
3. The same file runs `journal.total_spend` over these events: completions costing `1.25` and `0.5` usd, an `effect_intent` carrying a cost of `9` usd, a completion whose `cost` is a string, a completion with no `cost`, and a completion whose cost dict has no `usd`. It returns `1.75`, not `10.75` and not a `KeyError`. `total_spend([])` returns `0`.
4. The same file builds `config` with `state_dir = tmp_path`, one provider whose `auth` is `KEY`, and a `release.pypi_token`, then calls `enginelog.engine_log(config, {"KEY": "s3cret-value"}, clock)` with a fixed aware clock. The returned `EngineLog` has `path == tmp_path / "engine.log"`. After `.event("probe", detail="s3cret-value")`, that file contains `[REDACTED:KEY]` and not `s3cret-value`, so a factory that ignores `env` fails.
5. `tests/integration/test_projection_helpers_source.py` parses every `clutch/**/*.py` with `ast`. It fails, naming file and line, on each of these: (a) an `EngineLog(...)` call outside `enginelog.engine_log` and `driver.Driver.from_config`; (b) a `/` whose right operand is the string `"box"`; (c) outside `clutch/tickets.py`, an f-string whose `ast.unparse` text matches `tickets/\{[^}]+\}/ticket\.md`, or a chain of `/` whose operands include both `"tickets"` (bare or as `Path("tickets")`) and `"ticket.md"`; (d) in `clutch/observe.py` and `clutch/__main__.py`, a dict comprehension keyed by `<x>["ticket"]` or `<x>.ticket`, or an assignment to `<y>[<x>["ticket"]]` or `<y>[<x>.ticket]`; (e) in `clutch/observe.py`, a `SimpleNamespace(...)` call with a `type=` keyword outside `as_events`; (f) a `sum(...)` call whose argument contains the string constant `"usd"`, outside `journal.total_spend`. On the base commit it finds 8 `EngineLog` calls outside the two allowed functions, 6 `"box"` joins, 13 ticket paths, 4 folds, 4 wraps and 3 usd sums, so it fails there. It flags none of `(repo / "tickets").glob("*/ticket.md")`, `p / "ticket.md"` or `stats.py`'s per-surface `+=`. Checked by `./dev.py test tests/integration/test_projection_helpers_source.py`.
6. `./dev.py test tests/unit/test_phase_events.py tests/unit/test_verdict_extension.py` passes. Only the patch lines named in Scope in changed, so phase and refusal events still reach the patched log through `engine_log`.
7. The existing suites pass with no assertion changed: `./dev.py test tests/integration/test_daemon_composition.py tests/integration/test_watch.py tests/integration/test_watch_surface_tier.py tests/integration/test_status.py tests/integration/test_stats.py tests/unit/test_stats.py tests/integration/test_retro.py tests/unit/test_retro_measurements.py tests/integration/test_scan_owners.py tests/integration/test_main_verb_groups.py tests/integration/test_ask.py tests/integration/test_triage.py tests/integration/test_roadmap_status.py` exits 0. This includes the `redactor` trace in `test_daemon_composition.py`, which fails if a site makes a second `Redactor.from_config` call.
8. `uv run ruff check .` exits 0.

## Verification
```
./dev.py test tests/unit/test_projection_helpers_single_owner.py tests/integration/test_projection_helpers_source.py
./dev.py test tests/unit/test_phase_events.py tests/unit/test_verdict_extension.py tests/unit/test_stats.py tests/unit/test_retro_measurements.py
./dev.py test tests/integration/test_daemon_composition.py tests/integration/test_watch.py tests/integration/test_watch_surface_tier.py tests/integration/test_status.py tests/integration/test_stats.py tests/integration/test_retro.py tests/integration/test_scan_owners.py tests/integration/test_main_verb_groups.py tests/integration/test_ask.py tests/integration/test_triage.py tests/integration/test_roadmap_status.py
uv run ruff check .
```

## Definition of rejected
- A verb's output, the `clutch watch` text or the snapshot JSON changes for a journal whose transitions all carry `to`.
- A hand-written copy of an owned fold, wrap, sum, path or construction stays in a fenced file, or a compatibility alias keeps `EngineLog` or `Redactor` bound in `drain.py`, `runner.py` or `serve.py` for tests.
- `Driver.from_config` changes, a site makes a second `Redactor.from_config` call, or `tests/integration/test_daemon_composition.py` or `tests/integration/test_watch.py` is edited.
- An existing assertion changes, or `queue` or `running_stems` changes signature.
- A left-out item (attempt counting, the frontmatter readers, de-duplicating `storm_producer` construction) is touched beyond the `root=` argument edit in `build_control`, or `clutch/driver.py`, `clutch/tickets.py` or `clutch/caps.py` is edited.

## Time budget
- expected: 25m
- stuck: 50m
