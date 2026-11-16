---
state: confirmed
source: human
priority: P1
kind: feature
---

## Depends on
- release-at-gate
- roadmap-author
- roadmap-status

## Context
- docs/roadmap-driver-plan.md#6. The loop
- docs/roadmap-driver-plan.md#Open decisions
- clutch/roadmap.py
- clutch/notify.py::notification_key
- clutch/notify.py::send
- clutch/status.py::reject_queue
- clutch/status.py::project
- clutch/journal.py::TERMINAL_STATES
- clutch/effects.py::Effects
- clutch/seams.py::CommandNotifications
- clutch/serve.py::Serve.select
- clutch/serve.py::Serve.retro_pending
- clutch/serve.py::Serve.run_retro
- clutch/serve.py::Serve.run
- clutch/drain.py::drain
- clutch/drain.py::_Drain.run
- clutch/drain.py::_Drain._run_retro
- clutch/drain.py::_Drain._between_tickets
- tests/unit/test_drain_report_intake.py
- tests/unit/test_phase_events.py
- tests/integration/test_roadmap_author.py::setup_repo
- tests/integration/test_drain.py::pause_checkout
- tests/integration/test_drain.py::Script
- tests/integration/serve_rig.py::graph
- tests/integration/serve_rig.py::script
- tests/integration/serve_rig.py::until
- tests/integration/serve_rig.py::finish
- docs/how-clutch-works.md#7.1
- docs/how-clutch-works.md#7.2
- docs/how-clutch-works.md#7.4

## On-demand
- clutch/__main__.py

## Goal / Why
Roadmap row 93 (`docs/roadmap.md`, owning design `docs/roadmap-driver-plan.md` section 6) is the loop that runs the roadmap unattended. Its pieces are merged:
- `roadmap author` (`clutch/roadmap.py::author_ahead`) files ready rows and links them;
- `roadmap status` reports progress, the last gate result, and the next rows;
- `release-at-gate` adds `clutch/roadmap.py::ship`, which runs the current release's gate, then `release --minor`, then `publish` only under `release.publish: true`.

Nothing runs them. Today a person types `clutch roadmap author` and `clutch release`. This ticket runs them at the engine's idle points and sends a digest after every settle (decision 4 of the plan's open decisions).

After this change, whenever `docs/roadmap.md` exists in the checkout, `drain` and `serve` run one driver step when they start and after every settle (each new terminal state transition). `run` never does. The step, in order:
1. `author_ahead(checkout, AHEAD, ...)` with `AHEAD = 2`, the `--ahead` default;
2. `ship(checkout)`;
3. a digest: the rows merged since the last digest, the Reject-queue stems and why, the `roadmap status` lines (which include the next rows to author), the lines of steps 1 and 2, and the spend. It is sent through `config.notify` as an effect, so a restart never sends one digest twice.

A `Refusal` from a step is a digest line, and the next settle tries again. This ordering is how release and publish run back to back on a clean tree: steps run only at idle points, after the merge and before any new admission, and `ship` checks publish's preconditions before it tags.

Departures from plan section 6, and why:
- **Release and digest run in `drain` too, not only in `serve`.** The plan gives `drain` only steps 1 and 2. This repo's engine log records 287 `engine_start` events, all `drain` and none `serve`, so a serve-only release step would never ship 0.3.0. One step function serves both.
- **Plan step 1 (supervise unsupervised Reject-queue stems) is not built here.** `supervisor-rework` already runs the supervisor inside `runner.drive` at every terminal where it applies. What reaches the Reject queue another way is rare. The journal holds 7 merge-stage routes of 190 routed terminals, and 1 `reject_arrival`. Supervising those at an idle point needs a worktree and fresh Effect keys outside `drive`, which no merged code provides. Those stems are released by the supervising agent loop through `clutch prompt diagnose` (plan open decision 5a; prompt rewritten by `drain-loop-agent`). A Suggestion Box message records the idle-point supervisor as a follow-up.
- **A host with `docs/roadmap.md` opts in by having the file.** There is no config flag. Without the file the step is skipped and serve's admission is never held for it, so hosts and the existing serve and drain tests are unchanged.

## Scope in / Scope out
Scope in:
- `clutch/roadmap.py`:
  - `AHEAD = 2`.
  - `settles(events) -> int`: the number of `STATE_TRANSITION` events whose `to` is in `clutch/journal.py::TERMINAL_STATES`.
  - `async def drive(checkout, *, author_messages, notifications, log) -> list[str]`:
    1. When `checkout.repo / ROADMAP` is not a file, return `[]` with no other call.
    2. Run `author_ahead(checkout, AHEAD, author_messages)` and then `ship(checkout)`, collecting their lines in that order. A `Refusal` from either becomes the one line `roadmap: <str(exc)>` (the refusal's message, ` -- `, and road), and the next step still runs. Any other exception propagates.
    3. Read `events = checkout.journal.read()`. `n = settles(events)`. `prior` is the largest integer `k` among `EFFECT_INTENT` keys of the form `notify/roadmap/digest/<k>` in `events`, or `n - 1` when there is none.
    4. The digest lines, in order:
       - `roadmap digest <n>`;
       - `merged: ` followed by the stems, joined by `, `, of `merged` transitions among terminal transitions numbered `prior + 1` to `n` (1-based, journal order), or `merged: none`;
       - `held: ` followed by `<stem> (<reason>)` for each `clutch/status.py::reject_queue(events)` entry in stem order, joined by `; `, or `held: none`;
       - the lines of `await status(checkout)`, or the one line `roadmap: <str(exc)>` when it raises `Refusal`;
       - the step lines from point 2;
       - `spend: $<x.xx>` from `clutch/status.py::project(events).spend_usd`.
    5. When `checkout.config.notify` is not None, `await clutch/notify.py::send(Effects(checkout.journal), notifications, checkout.config.notify, owner="roadmap", escalation="digest", identity=str(n), message="\n".join(digest), ticket=None)`. A `NotificationFailed` is logged as `log.event("notify_failed", key=<notification_key("roadmap", "digest", str(n))>, error=str(exc))` and not raised. When `notify` is None, nothing is sent and no effect is journaled.
    6. `log.event("roadmap_drive", lines=digest)`, then return the digest lines.
- `clutch/__main__.py`:
  - `build_driver()` returns `async def step(checkout, log) -> list[str]`, which calls `roadmap.drive` with the arguments below. `roadmap.drive`, `_preflighted_llm`, and `triage.triage_pass` are looked up on their modules at call time, so tests can replace them.
    - `author_messages(ids)`: `llm = await _preflighted_llm(checkout, checkout.control.providers)`, then `await triage.triage_pass(checkout, llm, frozenset(ids))`, as the `roadmap author` verb does;
    - `notifications`: a `CommandNotifications(SubprocessExec(), cwd=checkout.repo, env=child_env(checkout.env, checkout.config, serving=None), timeout=NOTIFY_TIMEOUT_S, scrub=Redactor.from_config(checkout.config, checkout.env).scrub)`, as `build_notifications` composes one;
    - the given `log`.
  - The drain composition (`DrainDispatch` in `main`) exposes `build_driver()`'s step as `_driver`, so `getattr(dispatch, "_driver")` returns that callable unbound.
  - `_parser`: the `roadmap author --ahead` default becomes `clutch.roadmap.AHEAD`, imported inside `_parser`, where the local `roadmap` names the subparser.
- `clutch/serve.py`, `Serve`:
  - `__init__` sets `self.driver = build_driver()` (imported from `clutch.__main__` beside `build_notifications`), `self.driven = None`, and `self.driver_task = None`.
  - `driver_pending()` is true when `self.checkout.repo / ROADMAP` is a file and `settles(self.checkout.journal.read()) != self.driven`.
  - `select` holds new admission while `driver_pending()`, in the same clause that holds it while `retro_pending()`, so continuations of writers already running still proceed.
  - `run`'s loop handles a driver task the way it handles the retro task. A finished task's `result()` is read, so its error stops serve as a retro error does. A new task `run_driver()` starts when `driver_pending()`, no retro task exists, `retro_pending()` is false, `self.upgrade is None`, no stop is requested, and `upgrade_idle()`.
  - `async def run_driver()`: under `self.mutations()`, return when stopping, stop-requested, or kill-requested. Otherwise build `c = replace(self.checkout, config=snapshot_config(self.control.load_config()))`, set `self.driven = settles(c.journal.read())`, and `await self.driver(c, self.log)`.
- `clutch/drain.py`:
  - `_Drain` has class attributes `driver = None` and `driven = None`, so instances made with `__new__` (as `tests/unit/test_drain_report_intake.py` makes one) still run.
  - `drain()` sets `run.driver = getattr(dispatch, "_driver", None)` next to `run.retro`.
  - `_Drain.run`, right after the retro block: when `self.driver` is not None, `self.c.repo / ROADMAP` is a file, `await self._between_tickets()` is true, and `settles(self.c.journal.read()) != self.driven`, set `self.driven` to that count and `await self._run_driver()`.
  - `_run_driver()` runs `self.driver(self.c, log)` as a task under `self._await_controlled`, as `_run_retro` runs the retro, with an abort that does nothing more than the task cancellation `apply_kill` performs. So a kill during the step stops it. `log` is an `EngineLog` built as `_run_retro` builds one.
- `docs/how-clutch-works.md`, four edits:
  - Section 7.1 step 2: after "maybe run a retro," insert "run the roadmap driver after a settle (section 7.5),".
  - Section 7.2: after the paragraph on requested and automatic retros, add one sentence. With `docs/roadmap.md` present, the roadmap driver (section 7.5) holds new admission at start and after each settle, runs at the next idle point after any retro, then resumes admission.
  - Section 7.4's Notifications bullet gains: "The roadmap driver sends a digest after every settle (section 7.5)."
  - A new section `### 7.5 Roadmap driver`, before `## 8.`, states:
    - when the step runs: drain and serve start and every settle, only with `docs/roadmap.md`, never in `run`;
    - its three steps, including the release boundary (the `pyproject.toml` version as `<major>.<minor>.0`) and that publish needs `release.publish: true`;
    - the digest's lines and its effect key `notify/roadmap/digest/<n>`, and that unset `notify` sends nothing;
    - the `roadmap_drive` engine-log event;
    - that a refusal becomes a digest line while any other error stops the engine;
    - that the Reject-queue supervisor runs inside `runner.drive` (section 6.6), not here.
  Nothing else in the file changes.
- `clutch/docs/host-running.md`: the `roadmap` verb-table row gains one sentence: when `docs/roadmap.md` exists, `drain` and `serve` run `roadmap author --ahead 2`, the release gate (releasing and, with `release.publish: true`, publishing when it passes), and a `notify` digest at start and after every settle.
- New tests in four new files: `tests/unit/test_roadmap_drive.py`, `tests/unit/test_driver_hooks.py`, `tests/integration/test_roadmap_driver.py`, and `tests/integration/test_serve_driver.py`. They may import, unchanged:
  - `MemoryJournal` from `tests/unit/test_retro_recurrence.py`, and `RecordingLog`, `install_log`, and `events` from `tests/unit/test_phase_events.py`;
  - `setup_repo` from `tests/integration/test_roadmap_author.py`, and `author_reply` and `requisition_reply` from `tests/integration/test_triage.py`;
  - `pause_checkout`, `Script`, `Clock`, `make_root`, `commit_ticket`, `confirmed`, and `journal` from `tests/integration/test_drain.py`;
  - `graph`, `script`, `write`, `until`, `finish`, and `terminals` from `tests/integration/serve_rig.py`.

Scope out:
- Supervising Reject-queue stems at idle points (see the departure above), and any change to `runner.py`, `rework.py`, or `caps.py`.
- `clutch/specs/ask/drain-loop.md`: `drain-loop-agent` rewrites it.
- `ship`, `choose`, `author_ahead`, `status`, `run_gate`, and `clutch/release.py`: called, not changed.
- A config flag, verb, journal signal, `clutch/help.py` entry, snapshot field, or extension change; `docs/roadmap.md` and the plans.
- Reordering gate commands to make the gate cheaper.

## Scope fence
- clutch/roadmap.py
- clutch/__main__.py
- clutch/serve.py
- clutch/drain.py
- docs/how-clutch-works.md
- clutch/docs/host-running.md
- tests/unit/test_roadmap_drive.py
- tests/unit/test_driver_hooks.py
- tests/integration/test_roadmap_driver.py
- tests/integration/test_serve_driver.py

## Acceptance criteria
1. `tests/unit/test_roadmap_drive.py::test_drive_order_and_digest` writes `docs/roadmap.md` under `tmp_path`. It fakes `roadmap.author_ahead` (returns `["authored x"]`), `roadmap.ship` (returns `["gate ok"]`), and `roadmap.status` (returns `["release 1.0.0: ...", "next: r"]`), each recording its call in one list. The `MemoryJournal` holds:
   - terminal transitions `a` merged, `b` `gate_failed` with `routed: reject_queue` and reason `premise`, and `c` merged;
   - one `EFFECT_COMPLETION` with cost `{"usd": 1.5}`.

   `config.notify` is `["say"]`, and a fake `Notifications` records each argv. It asserts:
   - the call order is `author_ahead(checkout, 2, author_messages)`, `ship(checkout)`, `status(checkout)`;
   - the one notification is `["say", message]`, and `message.splitlines()` is exactly `["roadmap digest 3", "merged: c", "held: b (premise)", "release 1.0.0: ...", "next: r", "authored x", "gate ok", "spend: $1.50"]`;
   - `drive` returns those lines;
   - the journal gained an `EFFECT_INTENT` and an `EFFECT_COMPLETION` keyed `notify/roadmap/digest/3`;
   - the fake log holds `roadmap_drive` with those lines.

   Ruled out: a different step order, a digest missing held stems, next rows, or spend, and a digest outside the effect seam.
2. `tests/unit/test_roadmap_drive.py::test_digest_since_last_digest`. After criterion 1's run, it appends a fourth terminal (`d` merged) and runs `drive` again: the message's second line is `merged: d`. A third run with no new terminal sends no new notification and journals no new intent, because the `notify/roadmap/digest/4` effect replays. Ruled out: repeating merged stems already digested, and a duplicate digest after a restart with no new settle.
3. `tests/unit/test_roadmap_drive.py::test_drive_edges`:
   - with no `docs/roadmap.md`, `drive` returns `[]`, calls no fake, sends nothing, and appends nothing;
   - with `author_ahead` raising `Refusal("dirty", "commit it")`, `ship` and `status` still run, and the digest holds `roadmap: dirty -- commit it`;
   - with `config.notify` None, nothing is sent and no effect event is journaled, but the lines are returned and logged;
   - a `NotificationFailed("boom")` from the fake is logged as `notify_failed` with key `notify/roadmap/digest/<n>` and error `boom`, and `drive` returns normally;
   - a `RuntimeError` from `ship` propagates.

   Ruled out: a missing roadmap driving the step, one refusal skipping later steps, a failed delivery stopping the engine, and an unexpected error swallowed.
4. `tests/unit/test_roadmap_drive.py::test_build_driver_composes` fakes `roadmap.drive`, `cli._preflighted_llm`, and `triage.triage_pass` (and may fake `cli.child_env` and `cli.Redactor.from_config`). `cli.build_driver()`'s step, called with a `SimpleNamespace` checkout (repo, env, config with `notify`, `control.providers`) and a log:
   - passes that log to `drive`, and a `CommandNotifications` whose `cwd` is the repo;
   - its `author_messages(["box-1"])` calls `_preflighted_llm(checkout, checkout.control.providers)` and then `triage_pass(checkout, llm, frozenset({"box-1"}))`.

   `cli._parser().parse_args(["roadmap", "author"]).ahead == roadmap.AHEAD == 2`. Ruled out: a second LLM composition, and an `--ahead` default that drifts from the driver's.
5. `tests/unit/test_driver_hooks.py::test_serve_driver_pending_and_run` uses `object.__new__(serve.Serve)`, as `tests/unit/test_phase_events.py` does. It asserts:
   - `driver_pending()` is false without `docs/roadmap.md`; with it, true while `driven` differs from `settles(...)` and false once they match;
   - `run_driver()` calls the fake `driver` once with a checkout whose `config` is the `load_config` snapshot and with `s.log`, sets `driven` to the settle count before the call, and makes no call when `stopping` is true.

   Ruled out: a pending driver on a host without a roadmap, a driver run with a stale config, and a run during stop.
6. `tests/unit/test_driver_hooks.py::test_drain_runs_driver_between_tickets` builds a `_Drain.__new__` instance as `tests/unit/test_drain_report_intake.py` does (logging through `install_log(monkeypatch, drain)`), with `docs/roadmap.md` under `tmp_path`, a recording `driver`, `_between_tickets` faked, and `_await_controlled` faked to await the task. It asserts:
   - one `run()` with `_between_tickets` true calls the driver once with `run.c`, and leaves `driven` at the journal's settle count;
   - a second `run()` with no new terminal does not call it;
   - with `_between_tickets` false, or without `docs/roadmap.md`, or with `driver` None, it is not called.

   Ruled out: a driver step inside a ticket's retry cycle, and a repeated step with no new settle.
7. `tests/integration/test_roadmap_driver.py::test_driver_step_authors_and_digests` uses `setup_repo` from `tests/integration/test_roadmap_author.py`. Its `config.yaml` gains `notify: [<sys.executable>, "-c", <code writing sys.argv[1] to <tmp_path>/digest.txt>]`, committed. `clutch.__main__.ProviderLLM` is patched to a `FakeLLM([author_reply("first-row"), requisition_reply("approve")])`. The checkout comes from `pause_checkout`. It asserts:
   - `asyncio.run(cli.build_driver()(checkout, log))` makes the last two commits `clutch(roadmap): author first-row` and `clutch(first-row): ticket`;
   - `digest.txt` starts with `roadmap digest 0`, holds `roadmap: authored row 1 first-row` and a `next:` line, and ends with a `spend: $` line;
   - the journal holds a completion keyed `notify/roadmap/digest/0`;
   - a second call with no new settle, given a `FakeLLM([])`, makes no model request, does not rewrite `digest.txt`, and leaves HEAD unchanged.

   Ruled out: a composition that never reaches the Author stage or `notify`, and a digest resent with no new settle.
8. `tests/integration/test_roadmap_driver.py::test_drain_calls_driver_at_start_and_after_each_settle` uses `make_root` with two confirmed tickets, `one` and `two` (`one` at higher priority), run by `Script` to `merged`, and a committed `docs/roadmap.md`. `cli.build_driver` is monkeypatched to return a recorder that stores `settles(checkout.journal.read())` and the last terminal's stem at each call. `main(["drain"], ...)` exits 0, and the recorded settle counts are `[0, 1, 2]`, the second taken after `one` settled and before `two` started. Without `docs/roadmap.md`, the recorder is never called. Ruled out: no driver in drain, a driver step mid-ticket, and a step on a host without a roadmap.
9. `tests/integration/test_serve_driver.py::test_serve_holds_admission_for_the_driver` uses `graph` and `script` from `tests/integration/serve_rig.py`, with a `docs/roadmap.md` file in the rig's repo and two tickets written with `write`. `rig.owner.driver` is replaced by a recorder that stores `settles(...)` and the stage calls made so far. It runs `rig.owner.run()` until both tickets have terminals, then calls `finish`. It asserts:
   - the recorder ran with settle counts `[0, 1, 2]`;
   - at the call recorded with count 1, the second ticket's `implement` had not yet been called;
   - without `docs/roadmap.md` the recorder is never called, and the stage calls match the run with the roadmap.

   Ruled out: serve admitting new work before the driver runs, and a driver on a host without a roadmap.
10. `./dev.py test tests/unit/test_drain_report_intake.py tests/unit/test_phase_events.py tests/unit/test_roadmap_author.py tests/unit/test_roadmap_status.py tests/integration/test_drain.py tests/integration/test_serve_dispatch.py tests/integration/test_serve_lifecycle.py tests/integration/test_serve_notify.py tests/integration/test_serve_admission.py tests/integration/test_serve_upgrade.py tests/integration/test_serve_kill.py tests/integration/test_retro.py tests/integration/test_roadmap_author.py tests/unit/test_host_running.py` exits 0 with those files unedited.
11. The docs command in `## Verification` exits 0: `docs/how-clutch-works.md` has a `### 7.5 Roadmap driver` heading before `## 8.` naming `notify/roadmap/digest/`, `release.publish`, and `roadmap_drive`, and the `roadmap` row of `clutch/docs/host-running.md` names `--ahead 2`.
12. The unit check (`clutch covgate` over `tests/unit`, the `unit` entry of `config.yaml` `review.mechanical`) passes with `clutch/roadmap.py` at or above `default = 90`, `clutch/serve.py` at or above 8, `clutch/drain.py` at or above 10, and `clutch/__main__.py` at or above 13.
13. `./dev.py test` exits 0.

## Verification
```
./dev.py test tests/unit/test_roadmap_drive.py tests/unit/test_driver_hooks.py
./dev.py test tests/integration/test_roadmap_driver.py tests/integration/test_serve_driver.py
./dev.py test tests/unit/test_drain_report_intake.py tests/unit/test_phase_events.py tests/unit/test_roadmap_author.py tests/unit/test_roadmap_status.py tests/integration/test_drain.py tests/integration/test_serve_dispatch.py tests/integration/test_serve_lifecycle.py tests/integration/test_serve_notify.py tests/integration/test_serve_admission.py tests/integration/test_serve_upgrade.py tests/integration/test_serve_kill.py tests/integration/test_retro.py tests/integration/test_roadmap_author.py tests/unit/test_host_running.py
uv run python -c "import pathlib; q = chr(96); t = pathlib.Path('docs/how-clutch-works.md').read_text(); s = t.split('### 7.5 Roadmap driver')[1].split('## 8.')[0]; assert all(w in s for w in ('notify/roadmap/digest/', 'release.publish', 'roadmap_drive')); h = pathlib.Path('clutch/docs/host-running.md').read_text(); row = next(line for line in h.splitlines() if line.startswith('| ' + q + 'roadmap' + q + ' |')); assert '--ahead 2' in row"
./dev.py test
```

## Definition of rejected
The branch is rejected if:
- a driver step runs in `run`, inside a ticket's retry cycle, while serve admits new work, or on a checkout without `docs/roadmap.md`;
- serve or drain behaves differently without `docs/roadmap.md`, or an existing test is edited;
- a `Refusal` from one step stops the later steps or the engine, or a non-refusal error is swallowed;
- the digest is sent outside `clutch/notify.py::send`, sent twice for one settle count, or sent while `notify` is unset;
- it changes `ship`, `choose`, `author_ahead`, `status`, `run_gate`, `clutch/release.py`, `runner.py`, or `clutch/specs/ask/drain-loop.md`;
- it adds a config field, verb, journal signal, `clutch/help.py` entry, or snapshot field, or edits `docs/roadmap.md`;
- a file outside `## Scope fence` changes.

## Time budget
- expected: 130m
- stuck: 180m
