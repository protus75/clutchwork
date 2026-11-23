---
state: draft
source: box:suggestion
priority: P0
kind: feature
agent_tier: medium
agent_effort: medium
---

## Depends on
none

## Context
- clutch/flake.py::Flake.release
- clutch/flake.py::Flake.detect
- clutch/flake.py::Flake.quarantine
- tests/integration/test_flake.py
- tickets/flake-release/ticket.md

## Goal / Why
A quarantined flake whose Box report was resolved as `declined` can never be released. `Flake.release` sets `fix` only for a `resolved` message whose resolution kind is `ticket`; any other resolution reaches `if fix is None: return projection`. Triage declined all five source reports (registry records 000359, 000449, 000450, 000451 and 000457) because they had no traceback, so the quarantine cap of 5 is full and unreleasable. `detect` then escalates "quarantine-cap crossed" and blocks every new flaky test (it blocked `meta-schema-and-refresh-r2` attempt 3). This breaks the CLAUDE.md rule that a hold ships with its release: this hold has no reachable release.

When this ticket is done, a quarantined test whose Box report carries a `declined` resolution is released by a supplied green rerun of that test, with no fix ticket and no merge. The release is journaled. A sixth `detect` after five such releases no longer escalates. A report resolved to a ticket still needs the merged fix as before. The class fix is the same change: every resolution kind that can close a report now has a reachable release path.

This does not re-solve `testguard-slowest-order-deterministic` (a different test) or `declined-box-000869` (test_budget_and_slowest, not in the cap).

## Boundary contract
### Flake release
- disposition: extend
- owner: clutch/flake.py (`Flake.release`)
- consumers: callers of `Flake.release` in the engine (grep `.release(` in clutch/) and `Flake.quarantine` replay
- observable change: for a detection whose Box message is `status == 'resolved'` with `resolution.kind == 'declined'`, `release` with a valid `GreenRerunEvidence` (matching test_id, result `pass`, `observed`, `same_workspace` and `unchanged_code` true, timezone-aware `observed_at`) appends a `flake_released` signal and returns a projection without that test. The record's `fix_stem` is the string `declined:<box_id>` and the key is `flake-release/<box_id>/declined:<box_id>`; the evidence's `fix_stem` must equal that string. No merge event is required because there is no fix ticket.
- compatibility: ticket resolutions keep today's rules unchanged (merge required, `observed_at >=` latest merge). Pending resolutions and `tombstone` resolutions still return the projection idle. Existing journal records parse unchanged; `quarantine()` replay needs no change because the new record has the same fields.
- acceptance: declined plus valid green rerun releases; declined with missing, failing, unobserved or mismatched evidence raises `FlakeError` with the existing release road; recorded declined releases replay idempotently and a changed resolution refuses with "conflicting release resolution".
- tests: new unit test file covering the cases above, including the cap scenario
- post-merge source of truth: clutch/flake.py

## Scope in / Scope out
Scope in: in `Flake.release`, compute the release identity from the message resolution. A `ticket` resolution gives `fix = link` and requires a merge as now. A `declined` resolution gives `fix = f"declined:{box_id}"` and requires no merge. Skip the `merges` check for the declined case only; keep every other evidence check. The replay branch (`box_id not in projection.active`) compares the recorded `fix_stem` with the same computed value. Update the one sentence in `docs/how-clutch-works.md` that says release needs a resolved fix ticket (if the document states it), and the `release` docstring. In `tests/integration/test_flake.py`, remove `'declined'` from the idle parametrization of `test_release_resolves_exact_box_identity`, because a declined report with green evidence whose `fix_stem` is not `declined:<box_id>` now raises `FlakeError` and the declined release is covered by the new unit test; change nothing else in that file.
Scope out: the Box triage policy that declines no-traceback reports, the detection path, the quarantine cap value, a new CLI verb, and any change to `tombstone` handling.

## Scope fence
- clutch/flake.py
- tests/unit/test_flake_declined_release.py
- tests/integration/test_flake.py
- docs/how-clutch-works.md

## Acceptance criteria
1. With a detected flake whose Box report is resolved `declined`, `release` given a valid green rerun appends one `flake_released` signal and the returned `Quarantine.tests` no longer contains the test; checked by `./dev.py test tests/unit/test_flake_declined_release.py`. A result that leaves the test active fails it.
2. Declined with `result='fail'`, `observed=False`, a different `test_id`, or `evidence=None` raises `FlakeError` and appends nothing; checked by `./dev.py test tests/unit/test_flake_declined_release.py`.
3. Five detections at `cap=5`, all declined, then released by green reruns: a sixth `detect` of a new test admits it and `escalate` is not called, not escalated; checked by `./dev.py test tests/unit/test_flake_declined_release.py`.
4. A ticket-resolved report still raises `FlakeError` for insufficient evidence when its fix has no merge event, and a pending or tombstone resolution returns the projection without a journal append (the integration test's idle parametrization now lists only those two; declined is covered by criteria 1-2); checked by `./dev.py test tests/integration/test_flake.py tests/unit/test_flake_declined_release.py`.
5. Calling `release` again after a declined release returns the same projection and appends nothing (replay is idempotent); checked by `./dev.py test tests/unit/test_flake_declined_release.py`.

## Verification
```
./dev.py test tests/unit/test_flake_declined_release.py tests/integration/test_flake.py tests/unit/test_flake_fix_order.py
```

## Definition of rejected
The branch is rejected if a declined report can be released without a passing, observed, same-workspace green rerun, if ticket-resolved releases lose the merge requirement, or if a new verb, flag or parallel release path is added.

## Time budget
- expected: 20m
- stuck: 40m
