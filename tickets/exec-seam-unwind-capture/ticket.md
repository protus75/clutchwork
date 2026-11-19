---
priority: P1
kind: feature
agent_tier: medium
agent_effort: medium
source: box:suggestion
state: draft
---

## Depends on
none

## Context
- clutch/seams.py::SubprocessExec.run
- clutch/seams.py::GroupExec
- clutch/providers.py
- clutch/docs/host-contract.md
- tests/integration/test_exec_seam_reap.py

## Goal / Why
When `SubprocessExec.run` unwinds on a timeout or outer cancellation with no line-consumer failure, the raised exception carries `process_capture` = (stdout, stderr), holding the bytes already read plus the drained remainder from `_kill_and_wait`. Today only the consumer-failure branch attaches it, so the bare `raise` drops the output. `CliAdapter.invoke` then falls back to ('', ''), a timed-out or killed provider call's end.json has empty stdout and stderr blobs, and harvest's `events_tail` (read from the newest stdout blob) is empty, so Diagnose sees none of the event stream of a stuck-killed Implement or Review. docs/evidence-trail-plan.md section 6 says killed or timed-out calls keep their partial raw bytes.

This is a gap read from the code and not yet observed in a live run (every end.json in this repo's store has exit.status ok), so this is filed as a feature. The new integration test is the first reproduction against a real child.

## Boundary contract
### Process-exec unwind capture
- disposition: extend
- owner: clutch/seams.py (SubprocessExec.run)
- consumers: clutch/providers.py CliAdapter.invoke, which already reads `process_capture` from the exception
- observable change: every unwind of `run` after spawn (timeout, cancellation) attaches `process_capture` to the raised exception; the exception type is unchanged
- compatibility: the consumer-failure path keeps its current behavior (capture on both exceptions, `raise exc from consumer_error`); successful runs and return values are unchanged
- acceptance: a real child that prints lines then hangs past the timeout raises TimeoutError whose `process_capture[0]` holds the lines
- tests: new integration test with a real child, and a new unit test that runs the new capture lines with fakes
- post-merge source of truth: clutch/seams.py and the process-exec paragraph of clutch/docs/host-contract.md

## Scope in / Scope out
Scope in: in the `except BaseException` handler of `SubprocessExec.run` in clutch/seams.py, build the capture from `stdout`/`stderr` plus the `_kill_and_wait` remainder on every unwind and set `exc.process_capture`; keep the consumer-error branch attaching it to `consumer_error` too. Update the `GroupExec` docstring in clutch/seams.py and the `on_stdout_line` sentence in clutch/docs/host-contract.md to say every unwind attaches the capture. Add a new integration test file, tests/integration/test_exec_seam_unwind_capture.py, with real children. Create a new unit test file, tests/unit/test_seams_unwind_capture.py, that runs the new unwind-capture lines (which sit under a coverage floor in `test-gate.toml`) with no real process: it monkeypatches `clutch.seams._spawn` to return a fake process whose pipes are fed through in-memory `asyncio.StreamReader`s, and fakes `_kill_and_wait` and `_reap`, then drives a timeout and an outer cancellation.

Scope out: providers.py, evidence store, harvest, the unbounded (`timeout=None`) path, and the existing hot test files.

## Scope fence
- clutch/seams.py
- clutch/docs/host-contract.md
- tests/integration/test_exec_seam_unwind_capture.py
- tests/unit/test_seams_unwind_capture.py

## Acceptance criteria
1. `./dev.py test tests/integration/test_exec_seam_unwind_capture.py` runs a real child that prints lines then sleeps past a short timeout; the raised `TimeoutError` has `process_capture[0]` containing those lines, not `AttributeError` or ('', '').
2. The same file cancels the `run` task from outside after the child printed lines; the `CancelledError` carries `process_capture` with those lines.
3. The same file asserts a child that prints to stderr then hangs yields the stderr text in `process_capture[1]`.
4. `./dev.py test tests/integration/test_exec_seam_reap.py` still passes, so reaping and the consumer-failure capture are unchanged.
5. `./dev.py test tests/unit/test_seams_unwind_capture.py` uses a fake process and fake `_kill_and_wait`/`_reap` (no real process), drives a timeout and an outer cancellation, and asserts `exc.process_capture` holds the fed stdout plus the drained remainder, not a missing attribute.

## Verification
```
./dev.py test tests/integration/test_exec_seam_unwind_capture.py tests/integration/test_exec_seam_reap.py tests/unit/test_seams_unwind_capture.py tests/unit/test_evidence_envelope.py
```

## Definition of rejected
The branch changes the exception type raised on timeout or cancellation, adds a second capture path outside `SubprocessExec.run`, or fakes the child in the new integration test instead of running a real process.

## Time budget
- expected: 15m
- stuck: 30m
