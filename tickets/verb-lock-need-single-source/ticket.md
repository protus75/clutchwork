---
state: confirmed
source: human
priority: P1
kind: chore
---

## Depends on
- none

## Context
- clutch/lockfile.py
- clutch/observe.py::lock_holder
- clutch/observe.py::uncommitted_tickets
- clutch/observe.py::snapshot
- clutch/__main__.py::_review
- clutch/__main__.py::_control
- clutch/__main__.py::_verdict
- clutch/runner.py::verdict
- clutch/docs/host-running.md
- docs/how-clutch-works.md#2.1 Verbs
- docs/how-clutch-works.md#10.1 Files

## On-demand
- clutch/docs/host-contract.md
- tests/integration/test_watch.py
- tests/integration/test_lockfile.py
- tests/integration/test_control_cli.py
- tests/integration/test_review_command.py

## Goal / Why
Several places each guess what the current holder of `.clutch/state/clutch.lock` is and what it can do. Each guess was written separately, and they have drifted apart:
- The snapshot (`clutch/observe.py::snapshot`) treats any live lock holder as an engine. It sets `engine` (the Tickets view's Stop button) and marks every lock-capable menu entry `"locked"` from that one fact. It learns the holder's verb only by parsing `ps` arguments.
- `_review` takes the lock only when anything under `tickets/<stem>/` has pending changes. The snapshot's `uncommitted_tickets` counts only `ticket.md`, and its Review menu ignores pending changes altogether.
- `_control` (stop, kill, pause, resume) and `_verdict` (confirm, reject) treat a `LockHeld` as "an engine is running" and publish a control or admission request. Only `drain` and `serve` publish a control identity and consume those requests (`consumer.publish()` in `clutch/drain.py` and `clutch/serve.py`). So while `triage`, `dismiss`, `retro` or a locked `review` holds the lock, the request reaches no engine.
- `clutch/docs/host-running.md` still says `review` takes the writer lock outright.

Two operator-visible bugs came from this drift on 2026-11-11: Review greyed out during a drain (`review-menu-committed-unlocked`), and Stop shown during `triage` (`engine-flag-only-drain-serve`). Those tickets fix the two instances. This ticket removes the cause: when the holder's verb or a verb's lock need is decided in only one place, the snapshot and the verbs cannot disagree.

When this ticket is done:
- The lockfile records the holder's verb. Readers take the verb from there and never parse process arguments.
- One constant names the engine verbs that consume control requests (`drain`, `serve`). The snapshot's `engine` flag, `_control`, `_verdict` and `_retro` all read it.
- One predicate answers "does `tickets/<stem>/` have pending changes". `_review` uses it to decide whether to take the lock, and the snapshot uses it for the Review menu.

## Scope in / Scope out
- In: `Lockfile` takes the holder's verb and writes it as `verb` in its JSON identity. Every `Lockfile(...)` call site passes its verb, and every test that builds a `Lockfile` is updated. The eval call sites (`eval/harness.py` twice, `eval/diagnose.py` once) record verb `eval`, which is not an engine verb.
- In: the `clutch/lockfile.py` module docstring and the `clutch/docs/host-contract.md` sentence that call the recorded identity diagnostics only, never read for a decision. Both now say the recorded `verb` is read to decide whether the holder consumes control requests, while `flock` alone still governs correctness.
- In: one engine-verb constant (`drain`, `serve`) in `clutch/lockfile.py`.
  - The snapshot sets `engine` from the recorded verb.
  - The snapshot builds its `lock` string from the recorded verb and drops the `ps` argument parse for it. `processes` stays where other code still uses it.
  - `_control`, `_verdict` and `_retro`, on `LockHeld` when the recorded holder is not an engine verb, refuse. The refusal names the holder, with the paved road "wait for `<verb>` to finish, then retry". They do not publish a request.
- In: one lock-need predicate for a stem (any pending change under `tickets/<stem>/`, the test `_review` uses today), shared by `_review` (whether to take the lock) and the snapshot's `clutchReview` availability.
- Stays: `clutch/observe.py::uncommitted_tickets`. It answers a different question: whether the `ticket.md` content that intake and a verdict admit is committed. It keeps feeding the `committed`, `draft` and `new` row fields and the `clutchConfirm`/`clutchReject` menu unchanged.
- In: `clutch/docs/host-running.md` (the sentence listing verbs that take the writer lock outright: `review` takes it only for pending ticket changes) and `clutch/docs/host-contract.md` (the lockfile identity fields gain `verb`). Also `docs/how-clutch-works.md`: the `clutch.lock` row in section 10.1, and the `stop`, `kill`, `confirm`, `reject` and `retro` rows in section 2.1 for the non-engine-holder refusal.
- Out:
  - Reporting `.clutch/state/commit.lock` in the snapshot: it is held for seconds and has no operator action.
  - The extension (`vscode-clutchwork/`): the snapshot fields keep their names and closed values.
  - Changing which verbs take the writer lock. Run, triage, dismiss, retro, drain and serve still take it outright.

## Scope fence
- clutch/lockfile.py
- clutch/observe.py
- clutch/__main__.py
- clutch/runner.py
- clutch/drain.py
- clutch/serve.py
- clutch/docs/host-running.md
- clutch/docs/host-contract.md
- docs/how-clutch-works.md
- eval/harness.py
- eval/diagnose.py
- tests

## Acceptance criteria
1. `tests/integration/test_lockfile.py`: after `Lockfile(..., verb="triage").acquire()`, the JSON in `clutch.lock` has `"verb": "triage"`, not a missing key.
2. `tests/integration/test_watch.py`: with a live holder whose recorded verb is `triage` and whose `ps` arguments name `drain`, `snapshot(ctx)["engine"]` is `False` and `lock` starts with `triage since`. This proves the snapshot reads the recorded verb, not the process arguments.
3. `tests/integration/test_watch.py`: with a drain holding the lock, an open valid row whose `tickets/<stem>/evidence/` file is modified while `ticket.md` is committed gets `clutchReview == "locked"`, not `"on"`. This is the same pending-changes answer that makes `_review` take the lock.
4. `tests/integration/test_control_cli.py`: `stop` while a `triage` holder holds the lock exits non-zero with a refusal naming `triage`. It publishes no file under `control/inbox/`, not a request with no consumer. `stop` while a `drain` holder holds the lock still publishes its request.
5. `tests/integration/test_review_command.py` (or `tests/integration/test_cli.py` for `confirm`): `confirm` with a `triage` holder refuses naming `triage` and publishes no admission request.
6. New `tests/unit/test_lock_holder.py`, fake-backed with no subprocess:
   - The engine-verb decision is true for recorded verbs `drain` and `serve`, and false for `triage`, `eval` and a missing `verb` key.
   - `_control` (`stop`), `_verdict` (`confirm`) and `_retro`, with a held lock whose recorded verb is `triage`, raise a refusal naming `triage` and publish nothing.
   - With recorded verb `serve` they publish one request.
7. `./dev.py test` exits 0, which includes the `test-gate.toml` coverage floors for `clutch/lockfile.py`, `clutch/__main__.py`, `clutch/runner.py`, `clutch/drain.py` and `clutch/serve.py`.
8. `rg -n '"-m", "clutch"' clutch/observe.py` finds no match: the `ps` argument parse for the holder verb is gone.
9. `rg -n 'never read for a decision|diagnostics only' clutch/lockfile.py clutch/docs/host-contract.md` finds no match.

## Verification
```
./dev.py test
```

## Definition of rejected
- A second list of engine verbs remains beside the shared constant, or a second lock-need test for review remains beside the shared predicate.
- The holder verb is still derived from process arguments anywhere.
- Any verb's lock behavior changes, other than the refusal for a non-engine holder in `_control`, `_verdict` and `_retro`.
- Logic moves into `vscode-clutchwork/` JavaScript.

## Time budget
- expected: 60m
- stuck: 150m
