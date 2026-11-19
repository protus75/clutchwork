---
state: draft
source: box:suggestion
priority: P1
kind: feature
---

## Depends on
none

## Context
- clutch/roadmap.py::rejection_reason
- clutch/runner.py::failure_terminal
- tests/unit/test_roadmap_rejection_reason.py

## Goal / Why
When Diagnose or Rework splits a ticket and the replacement tickets fail review, `failure_terminal` sets verdict `reject` and parks the run, but it journals only the original failure's finding codes. The rework review's finding messages go only to `tickets/<stem>/attempts/<n>/harvest.json` or the box. `roadmap.py::rejection_reason` reads journal events alone, so the roadmap driver re-files the row without them and the next Author repeats the same split mistakes (seen in serve-parallel-dispatch-r1, attempts 0 and 1: stuck budget not twice expected, fence gaps, a missing seam). After this ticket, the failed rework's finding messages are on the journaled Reject-queue terminal event and `rejection_reason` appends them to the re-file summary.

## Boundary contract
### Reject terminal event body
- disposition: extend
- owner: clutch/runner.py (failure_terminal writes the terminal STATE_TRANSITION body)
- consumers: clutch/roadmap.py::rejection_reason; tests/integration/test_daemon_composition.py, which asserts the routed terminal body by dict equality and is updated in this change; other readers of terminal bodies (drain, status, stats, retro, observe) read only named keys and ignore a new one
- observable change: when rework was requested, the rework result is not ok, and the terminal is routed to the Reject queue (the branch that sets `terminal["routed"] = "reject_queue"`), the terminal body gains `rework_findings`, a list of `"<message>; <paved_road>"` strings from the failed rework's findings (the same `extra` list failure_terminal already builds). Absent otherwise, including mechanical terminals such as `render_over_bound`, which are not routed to the Reject queue.
- compatibility: existing events without the key stay valid; `rejection_reason` output is unchanged when the key is absent; mechanical terminal bodies are unchanged
- acceptance: a journaled Reject-queue terminal for a failed rework carries the messages; the key is absent when rework succeeded, was not requested, or the terminal is mechanical
- tests: new unit test calling failure_terminal with a fake context and a failed rework result; new integration test through failure_terminal with a real repo; updated expectation in test_daemon_composition.py
- post-merge source of truth: clutch/runner.py::failure_terminal

### Roadmap re-file reason
- disposition: extend
- owner: clutch/roadmap.py::rejection_reason
- consumers: the two roadmap driver re-file call sites that call rejection_reason
- observable change: the returned reason includes the latest routed terminal's `rework_findings` after its `reason`, before diagnosis lessons
- compatibility: events without the key give the same string as before
- acceptance: events with the key give a summary containing each message
- tests: new unit test over hand-built events
- post-merge source of truth: clutch/roadmap.py::rejection_reason

## Scope in / Scope out
In: add `rework_findings` to the terminal body in `failure_terminal` only in the branch that routes the terminal to the Reject queue, when `rework_requested` and the rework result is not ok; read it in `rejection_reason`; add the three new test files. The new unit test file `tests/unit/test_runner_rework_findings_terminal.py` runs the new runner.py lines with the same fake-context pattern as `tests/unit/test_supervise_merge_route.py` (a fake context and a hand-built failed rework StageResult, no real repo, process or network); the real-repo checks stay in `tests/integration/test_rework_failure_terminal_findings.py`. In `tests/integration/test_daemon_composition.py` only the routed-terminal expectation near line 1361 changes: it gains the `rework_findings` key with the failed rework's message strings. The existing `tests/unit/test_roadmap_rejection_reason.py` stays unchanged and must still pass. Mechanical terminals (`render_over_bound` in tests/integration/test_diagnose.py and tests/integration/test_drain.py) get no key, so those tests stay unchanged.
Out: harvest and box behavior, Diagnose and Rework specs, the drain report (covered by drain-park-shows-review-findings), diagnosis lessons carry (refile-carries-diagnosis), operator reason carry (operator-reject-reason-refile), and docs.

## Scope fence
- clutch/roadmap.py
- clutch/runner.py
- tests/unit/test_roadmap_rejection_reason_rework_findings.py
- tests/unit/test_runner_rework_findings_terminal.py
- tests/integration/test_rework_failure_terminal_findings.py
- tests/integration/test_daemon_composition.py

## Acceptance criteria
1. `rejection_reason` over a routed terminal with `reason: "x"` and `rework_findings: ["fence gap; add path"]` returns a string containing `fence gap; add path`, not just `x`; checked by `./dev.py test tests/unit/test_roadmap_rejection_reason_rework_findings.py`.
2. `rejection_reason` over a terminal without `rework_findings` returns exactly what it did before (`"later"` for the existing case, `"rejected"` for no events); checked by `./dev.py test tests/unit/test_roadmap_rejection_reason.py`.
3. After `failure_terminal` runs with `rework_requested=True` and a rework result whose outcome is `snag` with findings, and the terminal is routed to the Reject queue, the journaled terminal body's `rework_findings` contains each finding's message, not an empty list or missing key; checked by `./dev.py test tests/integration/test_rework_failure_terminal_findings.py`.
4. After `failure_terminal` with a successful rework (`ok`), with `rework_requested=False`, or with a mechanical `render_over_bound` terminal after a failed rework, the terminal body has no `rework_findings` key; checked by `./dev.py test tests/integration/test_rework_failure_terminal_findings.py`.
5. The failed-rework-publication cases in `tests/integration/test_daemon_composition.py` still pass with the routed terminal body expectation including `rework_findings`, and the mechanical `render_over_bound` assertions in `tests/integration/test_diagnose.py` and `tests/integration/test_drain.py` pass unedited; checked by `./dev.py test tests/integration/test_daemon_composition.py tests/integration/test_diagnose.py tests/integration/test_drain.py`.
6. `runner.failure_terminal` called with a fake context and a failed rework `StageResult` (not ok, with findings) that routes to the Reject queue journals a body whose `rework_findings` lists each finding's `"<message>; <paved_road>"` string, not a missing key or an empty list; with an ok rework result, or `rework_requested=False`, the body has no `rework_findings` key; checked by `./dev.py test tests/unit/test_runner_rework_findings_terminal.py`.

## Verification
```
./dev.py test tests/unit/test_roadmap_rejection_reason.py tests/unit/test_roadmap_rejection_reason_rework_findings.py tests/unit/test_runner_rework_findings_terminal.py tests/integration/test_rework_failure_terminal_findings.py tests/integration/test_daemon_composition.py tests/integration/test_diagnose.py tests/integration/test_drain.py
```

## Definition of rejected
The findings are carried by a new journal event type, a second reader path, or a change to harvest or box output instead of the terminal body and `rejection_reason`; or the reason string changes when `rework_findings` is absent; or a mechanical terminal body gains the key.

## Time budget
- expected: 25m
- stuck: 50m
