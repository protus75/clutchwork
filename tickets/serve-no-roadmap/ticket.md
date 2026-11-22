---
state: confirmed
source: human
priority: P1
kind: chore
---

## Depends on
- none

## Context
- docs/roadmap-driver-plan.md#6. The loop (`driver-loop`)
- clutch/roadmap.py::author_ahead
- clutch/roadmap.py::ship
- clutch/roadmap.py::ship_when_queue_low
- clutch/roadmap.py::drive
- clutch/serve.py::Serve.driver_pending
- clutch/serve.py::Serve.run_driver
- clutch/serve.py::Serve.wait_driver
- clutch/__main__.py::build_driver
- clutch/drain.py::_Drain._run_driver

## On-demand
- clutch/specs/ask/plan-ticket-serve.md
- clutch/specs/ask/plan-ticket-drain.md
- clutch/specs/ask/drain-loop.md
- docs/how-clutch-works.md
- clutch/docs/host-running.md
- clutch/docs/host-contract.md

## Goal / Why
Owner decision 2026-11-22: the engine process (`clutch engine serve` and `clutch engine drain`) has no roadmap knowledge. Running the roadmap is the job of a separate agent, the session started from `clutch prompt plan-ticket-serve` or `plan-ticket-drain`, using clutch verbs.

Today serve and drain each build a roadmap driver (`build_driver`), start it after every settle (`run_driver`, `driver_pending`, `driver_task`), and it authors rows ahead, runs the release gate, ships, and sends a digest. That puts the roadmap in the engine's dispatch loop: the author pass and the gate hold up the next dispatch, the engine reads `docs/roadmap.md`, and the plan-ticket prompts must work around the driver ("leave it nothing to author", "the driver runs the gate after every settle").

After this ticket neither process imports `clutch.roadmap` or reads `docs/roadmap.md`. The operator verbs stay (`clutch roadmap author`, `status`, `gate`, `merged`, `accept`, `clutch release bump`, `clutch release publish`, new `clutch release ship`) and the agent prompts own when to author rows and when to run the gate (only once the queue has drained). Shipping becomes one operator verb, `clutch release ship`, which the agent never runs: when the queue is drained and the release's rows are merged, the agent reports that the release is ready and names `clutch release ship` for the owner.

## Boundary contract

### Engine roadmap step in serve and drain
- disposition: replace
- owner: clutch/serve.py and clutch/drain.py
- consumers: `clutch engine serve`, `clutch engine drain`, the plan-ticket agent prompts, `clutch/__main__.py` composition
- observable change: serve's loop and drain's between-ticket step never call a roadmap function, never read `docs/roadmap.md`, send no `roadmap/digest` notification and write no `roadmap_drive` engine-log event; serve's idle test no longer waits on a driver task, and drain no longer defers quiescence for a driver pass
- compatibility: old contract is "with `docs/roadmap.md` present the engine authors ahead, gates, ships and sends a digest after each settle"; the replacement contract is that an agent runs those verbs; no flag, shim or fallback keeps the old step; recovery is `git revert`; a host with `docs/roadmap.md` now gets nothing from the engine, which is intended
- acceptance: unit tests prove one serve dispatch/idle cycle and drain's between-ticket step complete with every `clutch.roadmap` function monkeypatched to raise
- tests: new unit files under tests/unit; the driver-pinning tests are deleted or edited
- post-merge source of truth: clutch/serve.py, clutch/drain.py, docs/how-clutch-works.md

### Roadmap module
- disposition: replace
- owner: clutch/roadmap.py
- consumers: `clutch roadmap author|status|gate|merged|accept` handlers in clutch/__main__.py, clutch/mergequeue.py and clutch/index.py (constant and parser only), the plan-ticket agent prompts
- observable change: `drive`, `ship_when_queue_low`, `unsettled`, `settles`, the digest and its notification, and the `roadmap_drive` log event are deleted. `roadmap author` no longer re-files a rejected row under a new `-rN` stem: a rejected, unstruck row is reported under `waits:` with its rejection reason and left alone. The `clutch roadmap author` verb, `status`, `gate`, `merged` and `accept` keep their behavior otherwise. `ship` is not deleted: it moves out of clutch/roadmap.py into the `clutch release ship` verb (next section)
- compatibility: removal of dead engine-only code and of the rejected-row re-file (owner rule: a rejected row is never auto-refiled; the verb must not re-file either); the re-file of a ready row whose stem is already named in the journal with no state, and of a declined row, is not a rejected-row path and is preserved. Consumers of the deleted names are the in-engine driver and its tests only
- acceptance: `roadmap author` leaves a rejected row's stem and the roadmap table byte-identical and files nothing for it; no `drive`, `ship`, or `ship_when_queue_low` attribute remains on `clutch.roadmap`
- tests: tests/unit/test_roadmap_author_rejected_row.py (new), edited roadmap unit tests
- post-merge source of truth: clutch/roadmap.py

### Release shipping by verbs
- disposition: replace
- owner: clutch/__main__.py (the `release ship` handler, in the `release` group beside `handle_release` and `handle_publish`), clutch/release.py
- consumers: the owner at the terminal; the plan-ticket agent prompts name it but never run it
- observable change: new verb `clutch release ship`; `roadmap.ship` moves into its handler in place (no second copy, no alias, no `ship` left on `clutch.roadmap`). It runs the current release's gate (`roadmap.run_gate` for `current_release`) and exits non-zero printing the failing gate lines when the gate fails or refuses when there is no current release; otherwise it bumps `--minor` and tags (`release.release`), journals the release (`release.journal_release`), publishes to PyPI only when `release.publish: true` (existing `release.publishable` and `release.publish`), then runs `release.run_packages` and prints each line, in that order. It takes the writer lock as `release bump` and `release publish` do (`_locked`)
- compatibility: `release bump` and `release publish` are unchanged (arguments, exit codes, journal signal); `release.release`, `journal_release`, `publish`, `publishable` and `run_packages` are reused unchanged; the engine never calls the verb
- acceptance: with a failing gate, `release ship` exits non-zero and bumps, publishes and runs nothing; with a passing gate it bumps, journals, publishes only when `release.publish` is true, then runs packages, in that order
- tests: tests/unit/test_release_ship_verb.py (new); tests/unit/test_roadmap_ship.py and tests/integration/test_roadmap_ship.py are edited to drive the verb instead of `roadmap.ship`
- post-merge source of truth: clutch/__main__.py, docs/how-clutch-works.md, clutch/docs/host-running.md

### Prompts owning the roadmap loop
- disposition: replace
- owner: clutch/specs/ask/plan-ticket-serve.md, clutch/specs/ask/plan-ticket-drain.md, clutch/specs/ask/drain-loop.md
- consumers: `clutch prompt plan-ticket-serve|plan-ticket-drain|drain-loop`, the agents they start
- observable change: the prompts state that the agent, not the engine, authors rows and runs the gate, and that the agent never ships: when the queue is drained and the release's rows are merged it reports the release ready and names `clutch release ship` for the owner, never running `release bump`, `release publish` or `release ship`. No sentence says the engine, the driver or serve authors rows, gates or ships. This is the process change CLAUDE.md "Keep shipped process prompts in sync" requires to land with the engine change
- compatibility: prompt text only; the rendered placeholders (`${state_dir}`) and kinds are unchanged
- acceptance: rendered prompts contain none of the removed driver sentences and contain the agent-owned authoring and gate steps and the report-and-name-`clutch release ship` step
- tests: tests/integration/test_ask_plan_drain.py, tests/integration/test_ask_plan_serve.py and the other prompt tests listed in Scope fence
- post-merge source of truth: the three prompt specs

### Config `roadmap.ahead`
- disposition: reuse
- owner: clutch/config.py
- consumers: `clutch roadmap author` default `--ahead`
- observable change: none in behavior; kept because `clutch roadmap author` still uses it as its default window. Only the clutch/config.py comment and the doc rows drop the clause "also the queue size below which the release gate runs"
- compatibility: preserved
- acceptance: `clutch roadmap author` with no `--ahead` still uses `config.roadmap.ahead`
- tests: tests/unit/test_roadmap_author.py
- post-merge source of truth: clutch/config.py

## Scope in / Scope out
Scope in:
- Engine-written `# clutch:meta` header lines: the engine's Check meta fill rewrites the header of each edited file after Implement. Those header changes are in scope; the implementer never edits them.
- clutch/serve.py: delete `driver_pending`, `run_driver`, `wait_driver`, the `driver`, `driven` and `driver_task` attributes, the driver clause of `upgrade_idle`, the two driver blocks of the dispatch loop, the `driver_error` handling after the loop, and the `roadmap` and `build_driver` imports.
- clutch/drain.py: delete `driver`, `driver_task`, `driven`, `_run_driver`, `_abort_driver`, the driver `finally` in `run`, the driver step between tickets, the two driver guards in the no-pick path, `run.driver = getattr(...)`, and the `roadmap` import.
- clutch/__main__.py: delete `build_driver` and `DrainDispatch._driver`. Keep the `roadmap author` handler. Add the `release ship` subcommand through `_command` in the `release` group (full help: does, reads, writes, lock, exits, examples), its `handle_ship` handler holding the moved `roadmap.ship` logic under `_locked`, and its entry in the `release` dispatch table; update the `release` group description and epilog to list it. `release bump` and `release publish` and their help are untouched. Update the `roadmap author` help only where it names the driver or the re-file.
- clutch/roadmap.py: delete `ship` (its body moves into `release ship`, not copied), `drive`, `ship_when_queue_low`, `unsettled`, `settles` and the imports they alone used. Delete the rejected-row loop of `author_ahead` (the `rejected` list, `reasons`, the `-rN` refile of a rejected row, its `re-files spent` line) and the helpers only it used. In `status`, a rejected unstruck row is listed under `waits:` with `rejection_reason`; keep `rejection_reason`, `fresh_stem`, `refile_row`, `refile_count` and `decline_reason` where the ready-row and declined-row paths still use them, and delete any left with no caller. The grep for each deleted name over clutch/, tests/ and docs/ is the checklist.
- Keep `clutch.roadmap.ROADMAP` and `parse`, which clutch/mergequeue.py and clutch/index.py use; the engine reads no roadmap content.
- clutch/config.py: keep `roadmap.ahead`; edit its trailing comment only.
- Prompts (the agent owns these steps; remove every sentence saying the engine, driver or serve authors rows, runs the gate after each settle, ships, or sends a digest):
  - plan-ticket-serve.md and plan-ticket-drain.md: Authoring: the agent fills the window with parallel row agents (`clutch prompt author <stem>`), never authors a row before every stem in its Depends on has merged, never authors ahead of the current release, and `clutch roadmap author` is a verb the agent may use to link rows and file the rest. Drop "The driver's author pass ... leave it nothing to author" and "the driver then only links rows". Replace "Never triage a `roadmap_row` Suggestion Box message; the driver owns it" with the `clutch roadmap author` verb owning it. Replace "publishing happens only through the driver under `release.publish: true`" with publishing only through `clutch release publish` under `release.publish: true`. Drop the `roadmap_drive` log line from Watch and the "serve exits with a driver error" and "drain ... driver error" bullets. Drop "Driver authoring ahead can keep a drain from quiescing" and "holds a slot of the driver's author-ahead window". Release step: in Closing each phase, run `clutch roadmap gate <release>` only after the queue has drained (nothing running or confirmed unrun), then, with the gate passed and the release's rows merged, report to the owner that the release is ready and name `clutch release ship`; never run `release bump`, `release publish` or `release ship`; the acceptance-review sentence stays. Replace "the driver runs the gate after every settle and ships at the first pass" with the agent running the gate once.
  - Remove the `clutch release bump --minor` bullet in Before you start; no prompt has the agent bump, publish or ship.
  - drain-loop.md: delete the paragraph "The engine already does this itself: ... authors roadmap rows ahead, release ... digest" and keep the supervisor-edits sentence; step 5 no longer reads `roadmap_drive` events: start a drain when a stem is eligible or `clutch roadmap status` shows a `next:` row the agent has authored; drop the "authored nothing" `roadmap_drive` clause; "A `roadmap_row` message ... the driver owns it" names `clutch roadmap author`.
- Docs (edit only the sections the change makes false):
  - docs/roadmap-driver-plan.md: add a dated decision note (2026-11-22) at section 6 that the loop is an agent using verbs and the engine runs none of steps 2-4; leave the rest of the plan as history.
  - docs/how-clutch-works.md: the serve and drain idle-step lists (about lines 510 and 556), the notification line about the digest (627), section 7.5 "Roadmap driver" (rewritten as the operator verbs and the agent-owned loop, no digest, no engine step, shipping by the owner's `release ship`), the `ship` mentions (133), the `roadmap author` verb row if it names the re-file of rejected rows, a new `release ship` row in the section 2 verb table, and the `roadmap.ahead` config row.
  - clutch/docs/host-running.md: the `roadmap` row sentence "When the roadmap table exists, `engine drain` and `engine serve` run ..." and a new `release ship` row.
  - clutch/docs/host-contract.md: "`ship` runs each configured package after the tag" becomes "`release ship` runs each configured package after the tag"; the `roadmap: {ahead: 2}` examples stay.
- Tests: delete tests whose subject is the removed driver step; edit tests that merely use a removed name; add the unit tests below.

Scope out:
- `clutch roadmap accept`, `gate`, `merged`, `status` (other than the rejected-row line), the supervisor step, retro, calibration, and the Suggestion Box triage in serve and drain.
- Removing the `release.packages` config or `release.run_packages`; changing `release bump` or `release publish`.
- The frozen bootstrap design record, the repo-root agent rule files and the roadmap table: none names the driver, none is edited.
- Stale driver wording in other guides and plan documents not listed in Scope in; those are separate Suggestion Box follow-ups.
- Rows or tickets for further roadmap automation; that belongs to the agent prompts.

## Scope fence
- clutch/serve.py
- clutch/drain.py
- clutch/__main__.py
- clutch/roadmap.py
- clutch/config.py
- clutch/specs/ask/plan-ticket-serve.md
- clutch/specs/ask/plan-ticket-drain.md
- clutch/specs/ask/drain-loop.md
- docs/roadmap-driver-plan.md
- docs/how-clutch-works.md
- clutch/docs/host-running.md
- clutch/docs/host-contract.md
- tests/unit/test_serve_no_roadmap.py
- tests/unit/test_drain_no_roadmap.py
- tests/unit/test_roadmap_author_rejected_row.py
- tests/unit/test_release_ship_verb.py
- tests/unit/test_roadmap_drive.py
- tests/unit/test_roadmap_ship.py
- tests/unit/test_roadmap_gate_waits_for_queue.py
- tests/unit/test_serve_driver_overlap.py
- tests/unit/test_drain_driver_overlap.py
- tests/unit/test_driver_hooks.py
- tests/unit/test_supervise_idle_hooks.py
- tests/unit/test_serve_dispatch_containment.py
- tests/unit/test_serve_verdict_owned.py
- tests/unit/test_git_main_write.py
- tests/unit/test_roadmap_author.py
- tests/unit/test_roadmap_refile.py
- tests/unit/test_roadmap_refile_ready.py
- tests/unit/test_roadmap_stuck_rows.py
- tests/unit/test_roadmap_named_stem.py
- tests/unit/test_roadmap_rejection_reason.py
- tests/unit/test_roadmap_rejection_reason_rework_findings.py
- tests/unit/test_roadmap_operator_reject_reason.py
- tests/unit/test_roadmap_release_audit_order.py
- tests/unit/test_release_packages.py
- tests/unit/test_ask_plan_drain.py
- tests/unit/test_ask_plan_serve.py
- tests/unit/test_ask_drain_loop.py
- tests/integration/test_roadmap_driver.py
- tests/integration/test_roadmap_ship.py
- tests/integration/test_roadmap_refile.py
- tests/integration/test_roadmap_named_stem.py
- tests/integration/test_roadmap_author.py
- tests/integration/test_serve_driver.py
- tests/integration/test_serve_driver_overlap.py
- tests/integration/test_serve_verdict_orphan_sweep.py
- tests/integration/test_reject_reason_both_paths.py
- tests/integration/test_ask_plan_drain.py
- tests/integration/test_ask_plan_serve.py
- tests/integration/test_ask_drain_loop.py
- tests/integration/test_ask_drain_loop_agent.py
- tests/integration/test_ask_plan_read_queue.py
- tests/integration/test_ask_plan_shared_paths.py
- tests/integration/test_ask_plan_subagent_models.py
- tests/integration/test_ask_plan_priority_order.py
- tests/integration/test_ask_plan_conduct_covered.py
- tests/integration/test_ask_depends_rule.py

## Acceptance criteria
1. `./dev.py test tests/unit/test_serve_no_roadmap.py` passes: with every public function of `clutch.roadmap` monkeypatched to raise, one serve dispatch and idle cycle completes, and the roadmap table file is never read; the test fails if `Serve` still has `driver_pending` or imports `clutch.roadmap`.
2. `./dev.py test tests/unit/test_drain_no_roadmap.py` passes: with every public function of `clutch.roadmap` monkeypatched to raise, drain's between-ticket step and no-pick exit complete, and a settle never starts a task or defers quiescence; it fails if `_Drain` still has `driver`, `driver_task` or `_run_driver`.
3. `./dev.py test tests/unit/test_roadmap_author_rejected_row.py` passes: for a rejected, unstruck row, `author_ahead` returns without a `refile` commit, the row's stem and the table stay byte-identical, no `roadmap_row` message is enqueued for it, and `status` lists it under `waits:` with its rejection reason; the test fails on the old behavior (a new `-r1` stem).
4. `./dev.py test tests/unit/test_release_ship_verb.py` passes: `clutch release ship` with a failing gate exits non-zero printing the failing command and bumps, publishes and runs no package; with a passing gate it bumps, journals, publishes only when `release.publish` is true, then runs packages and prints `package:` lines, in that order; it refuses when there is no current release; `clutch release --help` lists `ship` and `release ship --help` carries does, reads, writes, lock, exits and examples.
5. `grep -rnE "build_driver|\.run_driver|def run_driver|_run_driver|driver_pending|wait_driver|ship_when_queue_low|roadmap_drive|roadmap/digest|roadmap\.settles|roadmap\.unsettled|roadmap\.ship|roadmap\.drive" clutch tests docs/how-clutch-works.md clutch/docs` prints only the new no-roadmap tests (the moved implementation lives in clutch/__main__.py as the `release ship` handler and is not named `roadmap.ship`; the pattern names the removed serve and drain methods and does not match an unrelated bare local variable `run_driver` bound to `clutch.driver.Driver.run`, which stays), and `grep -nE "roadmap" clutch/serve.py clutch/drain.py` prints no `import` of `clutch.roadmap`.
6. `./dev.py test tests/integration/test_ask_plan_drain.py tests/integration/test_ask_plan_serve.py tests/integration/test_ask_drain_loop.py tests/integration/test_ask_drain_loop_agent.py` passes with the updated pins; the rendered prompts of `plan-ticket-serve`, `plan-ticket-drain` and `drain-loop` contain none of the strings "driver's author pass", "the driver runs the gate", "publishing happens only through the driver", "roadmap_drive" and contain `clutch roadmap gate` then `clutch release ship` (named as the owner's command, never as a step the agent runs) in Closing each phase of both plan prompts, and contain no instruction to run `clutch release bump`, `clutch release publish` or `clutch release ship`.
7. `./dev.py test tests/unit/test_roadmap_author.py` passes and its default-window case asserts `clutch roadmap author` with no `--ahead` uses `config.roadmap.ahead`, not a literal.
8. `./dev.py test` passes with the deleted driver tests removed and no remaining test asserting the old driver, ship or digest behavior.
9. `uv run clutch ticket lint serve-no-roadmap` exits 0, and `clutch/docs/host-running.md`, `clutch/docs/host-contract.md` and `docs/how-clutch-works.md` contain no sentence saying `engine serve` or `engine drain` authors rows, runs the release gate, ships, or sends a digest (checked in review by `grep -nE "digest|driver" ` on those files).

## Verification
```
./dev.py test tests/unit/test_serve_no_roadmap.py tests/unit/test_drain_no_roadmap.py tests/unit/test_roadmap_author_rejected_row.py tests/unit/test_release_ship_verb.py
./dev.py test tests/unit/test_roadmap_ship.py tests/integration/test_roadmap_ship.py tests/unit/test_roadmap_author.py tests/integration/test_ask_plan_drain.py tests/integration/test_ask_plan_serve.py tests/integration/test_ask_drain_loop.py tests/integration/test_ask_drain_loop_agent.py
./dev.py test
```

## Definition of rejected
- The engine still reads `docs/roadmap.md`, imports `clutch.roadmap` from serve or drain, or keeps any driver, digest or ship path behind a flag, an env var or a fallback; `release ship` exists as a second copy or alias beside a surviving `roadmap.ship`.
- `roadmap author` still re-files a rejected row as a new `-rN` stem.
- A prompt still says the engine, driver or serve authors rows, runs the gate after settles, ships, or sends a digest, or has the agent run `release bump`, `release publish` or `release ship`.
- The operator verbs `roadmap author|status|gate|merged|accept` or `release bump|publish` lose behavior other than the two stated here; `release ship` omits the gate, journal or packages step.
- New tests added to the hot test files, or driver-pinning tests rewritten to pass without proving the step is gone.

## Time budget
- expected: 55m
- stuck: 110m
- reason: one change cannot be split: removing the engine step, the prompts that describe it and the docs and tests that pin it must land together (CLAUDE.md "Keep shipped process prompts in sync"); most of the volume is deleting driver tests and rewriting prompt and doc sentences