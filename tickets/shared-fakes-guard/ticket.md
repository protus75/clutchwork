---
state: confirmed
source: human
priority: P0
kind: feature
---

## Depends on
- shared-review-script
- shared-serve-rig-config

## Context
- tickets/shared-review-script/ticket.md
- tickets/shared-serve-rig-config/ticket.md

## Goal / Why
`shared-review-script` moves the per-file model-reply helpers into `tests/stage_replies.py`, and `shared-serve-rig-config` moves the copied test `config.yaml` texts into `tests/config_fixture.py`. Their adoption tests check only the files they migrated, so nothing stops a new test from defining its own reply helper or pasting its own config text again. Those copies are what made engine changes break tests outside a ticket's fence. (The Git stand-ins already get a tree-wide guard from `shared-git-fake`'s adoption test.) After this ticket one integration test scans every Python file under `tests/` and fails when a file outside the shared modules defines a stage-reply helper or holds a full config text. An explicit exemption list carries a reason for each existing file that legitimately differs, and an exempt file that no longer matches also fails, so the list only shrinks.

## Boundary contract
### Shared test fake guard
- disposition: create
- owner: tests/integration/test_shared_fakes_guard.py
- consumers: Check's integration suite for every ticket
- observable change: a new test fails, naming the file and the shared module to import from, when a file under `tests/` other than `tests/stage_replies.py` defines `def requisition_reply(`, `def review_verdict(`, `def implement_reply(` or `def verdict(`, or when a file other than `tests/config_fixture.py` holds a string containing both `schema_version:` and `routing:`, unless the file is in that rule's exemption list
- compatibility: no production code changes; existing tests are unchanged
- closest existing: tests/integration/test_shared_stage_replies.py and tests/integration/test_config_fixture_adoption.py, which check only their own migrated files and are kept as they are
- earning reason: consolidation of evidenced duplicates; the per-file copies caused repeated out-of-fence failures (requisition-review-approval-reuse, requisition-contract-review-comparison, merge-dirty-checkout-never-blocks)
- acceptance: criteria 1 to 3
- tests: tests/integration/test_shared_fakes_guard.py
- post-merge source of truth: tests/integration/test_shared_fakes_guard.py

## Scope in / Scope out
Scope in:
- New tests/integration/test_shared_fakes_guard.py. It reads tracked test files through a `Path(__file__)` anchor (`tests/**/*.py`, skipping `tests/regress_*.py` reproducers, which run against the merge base and stay frozen). It holds two exemption dicts, `REPLY_EXEMPT` and `CONFIG_EXEMPT`, mapping a repo path to a one-line reason. Fill them with exactly the files that still match after the dependencies merge. Expected examples are `tests/integration/test_eval_harness.py` (a different finding shape), the inline copy in `tests/integration/test_scorecard.py`, and config-parsing tests such as `tests/integration/test_config.py`. Every entry needs a reason.
- The failure message names the file and the paved road: `import it from tests/stage_replies.py` or `build it with tests/config_fixture.py::build_config`.
Scope out:
- Migrating the exempt files, retiring `tests/fakes.py::FakeGit`, and the Git stand-in guard (owned by `shared-git-fake`).

## Scope fence
- tests/integration/test_shared_fakes_guard.py

## Acceptance criteria
1. `./dev.py test tests/integration/test_shared_fakes_guard.py` passes on the merged tree, with every exemption entry carrying a non-empty reason.
2. `./dev.py test tests/integration/test_shared_fakes_guard.py` proves the scan function, given in-memory file texts, reports a new file defining `def requisition_reply(` and a new file holding a `schema_version:` plus `routing:` string, and does not report `tests/stage_replies.py` or `tests/config_fixture.py`.
3. `./dev.py test tests/integration/test_shared_fakes_guard.py` proves an exempt path whose text no longer matches is reported as a stale exemption, so the list cannot keep dead entries.

## Verification
```
./dev.py test tests/integration/test_shared_fakes_guard.py tests/integration/test_shared_stage_replies.py tests/integration/test_config_fixture_adoption.py
```

## Definition of rejected
An exemption without a reason, a denylist of specific file names instead of the pattern scan, a skipped or xfailed check, or files outside the fence change.

## Time budget
- expected: 10m
- stuck: 20m
