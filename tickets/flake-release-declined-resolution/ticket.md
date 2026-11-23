---
state: confirmed
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
- tests/unit/test_stages_flake_coverage.py
- tickets/flake-release/ticket.md

## Goal / Why
A quarantined flake whose Box report was resolved as `declined` can never be released. `Flake.release` sets `fix` only for a `resolved` message whose resolution kind is `ticket`; any other resolution reaches `if fix is None: return projection`. Triage declined all five source reports (registry records 000359, 000449, 000450, 000451 and 000457) because they had no traceback, so the quarantine cap of 5 is full and unreleasable. `detect` then escalates "quarantine-cap crossed" and blocks every new flaky test (it blocked `meta-schema-and-refresh-r2` attempt 3). This breaks the CLAUDE.md rule that a hold ships with its release: this hold has no reachable release.

When this ticket is done, a quarantined test whose Box report carries a `declined` resolution is released by a supplied green rerun of that test, with no fix ticket and no merge. The release is journaled. A sixth `detect` after five such releases no longer escalates. A report resolved to a ticket still needs the merged fix as before. The class fix connects the real Check caller to the declined release path, so future declined reports can leave quarantine.

This does not re-solve `testguard-slowest-order-deterministic` (a different test) or `declined-box-000869` (test_budget_and_slowest, not in the cap).

## Boundary contract
### Flake release
- disposition: extend
- owner: clutch/flake.py (`Flake.release`)
- consumers: callers of `Flake.release` in the engine (grep `.release(` in clutch/) and `Flake.quarantine` replay
- observable change: for a detection whose Box message is `status == 'resolved'` with `resolution.kind == 'declined'`, `release` with a valid `GreenRerunEvidence` (matching test_id, result `pass`, `observed`, `same_workspace` and `unchanged_code` true, timezone-aware `observed_at`) appends a `flake_released` signal and returns a projection without that test. The record's `fix_stem` is the string `declined:<box_id>` and the key is `flake-release/<box_id>/declined:<box_id>`; the evidence's `fix_stem` must equal that string. No merge event is required because there is no fix ticket.
- compatibility: ticket resolutions keep today's rules unchanged (merge required, `observed_at >=` latest merge). Pending resolutions and `tombstone` resolutions still return the projection idle. Existing journal records parse unchanged; `quarantine()` replay needs no change because the new record has the same fields.
- acceptance: declined plus valid green rerun releases; declined with missing, failing, unobserved or mismatched evidence raises `FlakeError` with the existing release road; recorded declined releases replay idempotently and a changed resolution refuses with "conflicting release resolution".
- tests: direct release tests and a Check-path test covering a declined report with no merge, a ticket resolution with and without a merge, and a non-passing observation
- post-merge source of truth: clutch/flake.py

## Scope in / Scope out
Scope in:
- In `clutch/flake.py`, derive the release identity for a resolved message in one place and reuse it in the release and replay paths. A ticket resolution uses its linked stem and still requires a merge. A declined resolution uses `declined:<box_id>` and skips only the merge and its time comparison. Keep the passing, observed, same-workspace, unchanged-code, timestamp and identity checks. Update the release docstring.
- In `clutch/stages.py::_check_host_results`, use that same release identity when Check observes a passing quarantined test. Call `Flake.release` for a declined report with matching `GreenRerunEvidence` and no merge event. Preserve the merged-fix gate for ticket resolutions and leave pending and tombstoned reports quarantined. Missing, failed and skipped observations do not release a test.
- Keep the release-method cases in new `tests/unit/test_flake_declined_release.py` and remove declined from the idle parametrization of `test_release_resolves_exact_box_identity` in `tests/integration/test_flake.py`. Add `tests/unit/test_check_flake_declined_release.py` exercising the real Check loop with the fake Git, process result and journal pattern in `tests/unit/test_stages_flake_coverage.py`.
- Update the results-driven Check paragraph and the Flaky tests bullet in `docs/how-clutch-works.md` to describe both release cases.

Scope out: report triage, detection, the quarantine cap, and new commands.

## Scope fence
- clutch/flake.py
- clutch/stages.py
- tests/unit/test_flake_declined_release.py
- tests/unit/test_check_flake_declined_release.py
- tests/integration/test_flake.py
- docs/how-clutch-works.md

## Acceptance criteria
1. With a detected flake whose Box report is resolved `declined`, `release` given a valid green rerun appends one `flake_released` signal and the returned `Quarantine.tests` no longer contains the test; checked by `./dev.py test tests/unit/test_flake_declined_release.py`. A result that leaves the test active fails it.
2. Declined with `result='fail'`, `observed=False`, a different `test_id`, or `evidence=None` raises `FlakeError` and appends nothing; checked by `./dev.py test tests/unit/test_flake_declined_release.py`.
3. Five detections at `cap=5`, all declined, then released by green reruns: a sixth `detect` of a new test admits it and `escalate` is not called, not escalated; checked by `./dev.py test tests/unit/test_flake_declined_release.py`.
4. A ticket-resolved report still raises `FlakeError` for insufficient evidence when its fix has no merge event, and a pending or tombstone resolution returns the projection without a journal append (the integration test's idle parametrization now lists only those two; declined is covered by criteria 1-2); checked by `./dev.py test tests/integration/test_flake.py tests/unit/test_flake_declined_release.py`.
5. Calling `release` again after a declined release returns the same projection and appends nothing (replay is idempotent); checked by `./dev.py test tests/unit/test_flake_declined_release.py`.
6. `./dev.py test tests/unit/test_check_flake_declined_release.py` drives Check with a passing observation and a declined report, and asserts the release signal contains the matching `declined:<box_id>` identity and removes that test from quarantine without a merge. A release-method-only implementation fails this test. The same test file checks a skipped or missing observation remains quarantined, and a ticket-resolved case releases only after its fix merges.

## Verification
```
./dev.py test tests/unit/test_flake_declined_release.py tests/unit/test_check_flake_declined_release.py tests/integration/test_flake.py tests/unit/test_flake_fix_order.py
```

## Definition of rejected
The branch is rejected if a declined report can be released without a passing, observed, same-workspace green rerun, if ticket-resolved releases lose the merge requirement, or if a new verb, flag or parallel release path is added.

## Time budget
- expected: 20m
- stuck: 40m
