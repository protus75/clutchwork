---
state: draft
source: human
priority: P0
kind: feature
---

## Depends on
- none

## Context
- clutch/drain.py::sort_key
- clutch/drain.py::order_tickets
- clutch/drain.py::parallel_order
- clutch/drain.py::_soft_edges
- clutch/scheduler.py::Scheduler.__init__
- clutch/scheduler.py::Scheduler.dispatch_next
- clutch/__main__.py::build_daemon_core
- clutch/box.py::Resolution
- clutch/box.py::Message
- clutch/flake.py::Flake.detect
- clutch/flake.py::Flake.release
- tests/unit/test_chain_order.py
- docs/how-clutch-works.md#7. Drain and serve

## Goal / Why
A flaky test costs every ticket's Check until the fix for it merges: on 2026-11-22 Check for `implement-skips-full-suites` attempt 2 took 509 s because `test_serve_admission_refusal_keeps_main_green[integration]` failed once, so Check reran the whole 3602-test integration suite (89 s) and then ran it again on the merge base (137 s). The fix tickets existed but waited behind other work: `serve-live-keep-single-verdict` was confirmed at 19:53 and was still second in `.clutch/state/queue.json` at 02:47 while unrelated tickets took both slots.

`Flake.detect` (`clutch/flake.py`) files each confirmed flake as a Box `failure_report` with `stage: check`, `outcome: gate_failed` and `origin` set to the test id, and the canonical link from that report to its fix is the message's `resolution` with `kind: ticket` and `link: <stem>` (the link `Flake.release` already reads). After this ticket, a confirmed eligible ticket so linked from such a report is dispatched ahead of every other eligible ticket, whatever its priority or chain length, in both serve (`Scheduler.dispatch_next`) and the serial drain pick, so the flake stops being paid for as soon as possible.

## Boundary contract
### Dispatch order
- disposition: extend
- owner: clutch/drain.py `order_tickets` and `parallel_order`
- consumers: clutch/scheduler.py `Scheduler.dispatch_next`, the serial drain pick in clutch/drain.py, clutch/observe.py `simulate`
- observable change: both functions take a keyword `fixes: Set[str]`, defaulting to empty; a ticket whose stem is in `fixes` sorts ahead of every ticket not in it, before priority, chain length, authored age and stem, which still break ties within each group; `_soft_edges` still applies after sorting, so `## Runs before` still wins over the flake-fix lead
- compatibility: with empty `fixes` both orders are unchanged; `clutch/observe.py` `simulate` keeps calling `order_tickets` without `fixes`
- acceptance: criteria 1 and 2
- tests: tests/unit/test_flake_fix_order.py
- post-merge source of truth: clutch/drain.py

### Flake fix set
- disposition: create
- owner: clutch/drain.py `flake_fixes`
- consumers: clutch/scheduler.py `Scheduler.dispatch_next`, the serial drain pick in clutch/drain.py
- observable change: `flake_fixes(messages: Iterable[Message]) -> set[str]` returns `m.resolution.link` for every message with `message_class == "failure_report"`, `stage == "check"`, `outcome == "gate_failed"`, `status == "resolved"` and `resolution.kind == "ticket"`; pure, no I/O
- compatibility: Box message files and resolutions are only read
- acceptance: criterion 3
- tests: tests/unit/test_flake_fix_order.py
- post-merge source of truth: clutch/drain.py
- closest existing: `Flake.release` in clutch/flake.py reads the same resolution link for one box id under the writer lock and appends journal events; it cannot answer "which stems fix a flake" for a whole set without side effects
- earning reason: two production consumers (serve's scheduler and the serial drain pick) need the same set

### Scheduler flake fix source
- disposition: extend
- owner: clutch/scheduler.py `Scheduler`
- consumers: clutch/__main__.py `build_daemon_core`
- observable change: `Scheduler` gains the attribute `flake_fixes: Callable[[], Set[str]]`, defaulting to `lambda: set()` like `continuations` and `select`; `dispatch_next` passes `self.flake_fixes()` as `fixes` to `parallel_order` and `order_tickets`; `build_daemon_core` sets it to `flake_fixes` over `Box(checkout.config.state_dir / BOX_DIR, checkout.fs).messages()`, read on each dispatch
- compatibility: constructor signature unchanged; existing `Scheduler(...)` call sites need no edit
- acceptance: criteria 4 and 5
- tests: tests/unit/test_flake_fix_order.py
- post-merge source of truth: clutch/scheduler.py

## Scope in / Scope out
Scope in:
- clutch/drain.py: add `flake_fixes`; add the `fixes` keyword to `order_tickets` and `parallel_order`, leading each sort key with `t.stem not in fixes`; in the serial drain pick, pass `fixes=flake_fixes(...)` over the Box at `self.c.config.state_dir / BOX_DIR` read with `self.c.fs` to its `order_tickets` call, adding the `Box`, `BOX_DIR` and `Message` imports.
- clutch/scheduler.py: add the `flake_fixes` attribute and pass it in both branches of `dispatch_next`.
- clutch/__main__.py `build_daemon_core`: set `core.scheduler.flake_fixes` as above.
- docs/how-clutch-works.md section 7: in the "Pick order" item and the "Dispatch" item, say that a ticket linked as the fix of a confirmed flake report dispatches first, ahead of priority, chain and age.
- New tests/unit/test_flake_fix_order.py covering criteria 1–5 with in-memory tickets, stand-in `Message` objects and the scheduler fakes used by tests/unit/test_scheduler_write_queue_seams.py, under `tmp_path`.
Scope out:
- Linking a hand-written ticket to a flake report (no verb resolves a Box message to an existing ticket today); the flake quarantine cap; Check's rerun and merge-base runs; `clutch/observe.py` `simulate`; triage decisions on flake reports.

## Scope fence
- clutch/drain.py
- clutch/scheduler.py
- clutch/__main__.py
- docs/how-clutch-works.md
- tests/unit/test_flake_fix_order.py

## Acceptance criteria
1. `./dev.py test tests/unit/test_flake_fix_order.py` proves `parallel_order([p0_long_chain, p2_fix], {}, unsettled, fixes={"p2_fix"})` returns `p2_fix` first, not the P0 ticket, and that the same call without `fixes` returns the P0 ticket first.
2. `./dev.py test tests/unit/test_flake_fix_order.py` proves `order_tickets([p0, p2_fix], {}, fixes={"p2_fix"})` returns `p2_fix` first, not `p0`, and that a ticket naming `p2_fix` in `## Runs before` still sorts ahead of it.
3. `./dev.py test tests/unit/test_flake_fix_order.py` proves `flake_fixes` returns `{"fix-a"}` for a resolved check `failure_report` linked `kind: ticket` to `fix-a`, and excludes a pending report, a `declined` and a `tombstone` resolution, and a `failure_report` with `stage: implement`.
4. `./dev.py test tests/unit/test_flake_fix_order.py` proves that a `Scheduler` with `flake_fixes = lambda: {"fix"}` and parallel enabled dispatches `fix` (P2) before an eligible P0 ticket, and the written `queue.json` `order` begins with `fix`, not the P0 stem.
5. `./dev.py test tests/unit/test_flake_fix_order.py` proves that a `Scheduler` with `flake_fixes = lambda: {"fix"}` dispatches the eligible P0 ticket, not `fix`, in each of three cases: `fix` is `state: draft`, `fix` depends on an unsettled stem, and `fix` is in `quarantined()`.

## Verification
```
./dev.py test tests/unit/test_flake_fix_order.py tests/unit/test_chain_order.py
```

## Definition of rejected
- A flake-fix ticket that is not confirmed, has an unsettled dependency, or is held still dispatches (the lead must apply only inside the already-eligible set).
- `## Runs before` edges stop being honored for flake-fix tickets.
- Box messages are written, resolved or journaled by the ordering code.

## Time budget
- expected: 20m
- stuck: 40m
