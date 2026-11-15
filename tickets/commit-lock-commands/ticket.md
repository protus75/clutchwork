---
state: confirmed
source: human
priority: P1
kind: feature
---

## Depends on
- commit-lock
- intake-holds-commit-lock

## Context
- clutch/__main__.py::_review
- clutch/__main__.py::_verdict
- clutch/observe.py::lock_holder
- clutch/observe.py::snapshot
- vscode-clutchwork/media/view.js
- clutch/lockfile.py
- clutch/runner.py::verdict
- clutch/tickets.py::intake

## On-demand
- docs/how-clutch-works.md
- clutch/docs/host-running.md
- tests/integration/test_review_command.py
- tests/integration/test_control_cli.py
- tests/integration/test_watch.py

## Goal / Why
After `commit-lock`, every git write takes the short commit lock inside `clutch/git.py`. `review`, `confirm` and `reject` still treat the engine lock (`clutch.lock`) as a reason to refuse or to hand off, and the tickets view still greys them out whenever an engine runs.

On 2026-11-10, `./dev.py review core-template-budget` and `./dev.py review commit-lock` were both refused after an edit while a drain ran, and each review had to wait for the drain to commit the edit first. The view also greys Review on committed tickets, even though reviewing them never needed the lock.

After this change:
- `review` on an edited ticket commits it and reviews it while a drain runs.
- `confirm` and `reject` on an edited ticket commit it before handing off to the running engine.
- The view enables those three actions whenever the row allows them.
- The view header shows both locks.

## Scope in / Scope out
- In: `clutch/__main__.py`:
  - `_review` never takes `clutch.lock` and no longer calls `runner.reap`. When the ticket directory has pending changes, it runs intake, which holds the commit lock across its status read, stray check and commits (from `intake-holds-commit-lock`), then reviews the committed blob as today.
  - `_verdict`: when `runner.verdict` finds `clutch.lock` held and the stem's ticket directory has pending changes, it runs intake first. If intake refuses that stem, the command exits 2 with the intake findings and publishes no admission request. Otherwise it publishes the request as today. A `CommitLockTimeout` exits 2 through the top-level handler, and no request is published. Neither path reaps.
- In: `clutch/observe.py` `snapshot()`:
  - New top-level string field `commitLock`. It is empty when `<state>/commit.lock` is missing, empty, or names a pid that is not alive. Otherwise it is `<verb> since <time> (pid <pid>)`, built exactly like the existing `lock` field. Factor the verb rule so both fields use it.
  - Row menus:
    - `clutchReview` is `on` for an open, valid row whether or not an engine runs, and is never `locked`.
    - `clutchConfirm` and `clutchReject` are `on` for a draft or held row whether or not it is committed or an engine runs.
    - `clutchRun` stays `locked` while an engine runs.
    - Box rows' `clutchTriage` and `clutchDismiss` are unchanged.
  - The `lock` and `engine` fields are unchanged.
- In: `vscode-clutchwork/media/view.js`: the header shows two labelled padlocks, `engine` from `snap.lock` and `commit` from `snap.commitLock`, before the unchanged counts. Each shows `🔒` when its field is non-empty and `🔓` otherwise, with the field, or `unlocked`, as its hover title. The JavaScript only draws the two fields.
- In: documentation:
  - In `docs/how-clutch-works.md`: the verb table's lock column and text for `review`, `confirm` and `reject`.
  - In `clutch/docs/host-running.md`: the "Stop serve before ..." sentence no longer names `review`. In the verb table's `review` row, the "Works while serve runs?" cell becomes `Yes`, and its description says a pending edit is committed through intake before the review.
  - In `README.md`: the "Stop `serve` before `drain`, `run`, or `review`" sentence no longer names `review`.
- In: existing tests that pin the old lock behavior:
  - `tests/unit/test_stale_running.py` and `tests/integration/test_stale_running.py`: remove Review from the locked-verbs assertions (Review no longer takes `clutch.lock` or reaps). Keep every other verb's assertion.
  - `tests/unit/test_lock_holder.py`: its fake git gains `status_porcelain`, so the live-verdict tests pass through the new pending-change check. Keep its assertions.
- Out:
  - `triage`, `dismiss` and `migrate-box` keep the engine lock.
  - No `commit` verb.
  - No change to `vscode-clutchwork/package.json`, the `engine` field, or `clutch.engineRunning`.

## Scope fence
- clutch/__main__.py
- clutch/observe.py
- vscode-clutchwork/media/view.js
- docs/how-clutch-works.md
- clutch/docs/host-running.md
- tests/integration/test_review_command.py
- tests/integration/test_control_cli.py
- tests/integration/test_watch.py
- tests/unit/test_verdict_extension.py
- tests/unit/test_lock_holder.py
- tests/unit/test_stale_running.py
- tests/integration/test_stale_running.py
- README.md

## Acceptance criteria
1. `tests/integration/test_review_command.py`:
   - With `clutch.lock` held by a separate `Lockfile` and an edited ticket on disk, `review` approves, commits the edit (`main:` holds the new text), journals the verdict, and exits 0. It does not exit 2 with a lock refusal.
   - With `commit.lock` held past the wait (fake clock and sleep), `review` exits 2 naming `commit.lock`, and the ticket stays uncommitted.
   - With `clutch.lock` held and a journaled `running` stem, `review` of an edited ticket leaves that stem's last state `running`.
2. `tests/integration/test_control_cli.py`:
   - With `clutch.lock` held and an edited valid draft, `confirm --yes` commits the ticket and prints `confirm submitted:`.
   - With an edited invalid draft, it exits 2 with the intake finding and publishes no admission request.
   - With `commit.lock` held past the wait, it exits 2 naming `commit.lock` and publishes no admission request.
3. `tests/integration/test_watch.py`, with a live engine lock holder:
   - An open valid row's `clutchReview` is `on`, not `locked`.
   - A dirty held row's `clutchConfirm` and `clutchReject` are `on`, not `off`.
   - `clutchRun` stays `locked`, and pending box rows stay `locked` for triage and dismiss. Update the existing assertions that pinned `locked` and `off`.
   - `commitLock` is `""` with no `commit.lock`, and `""` with an empty one.
   - For a live holder whose command line is `python -m clutch review stem`, `commitLock` is `review since <clock(started_at)> (pid N)`.
4. `tests/unit/test_verdict_extension.py` keeps the `clutch/__main__.py` unit floor. With `runner.verdict` raising `LockHeld` and a fake git reporting pending changes for the stem:
   - A refused intake raises `Refusal`, and `control.publish_request` is never called.
   - A clean intake publishes exactly one request.
5. `./dev.py test tests/unit/test_verdict_extension.py tests/integration/test_review_command.py tests/integration/test_control_cli.py tests/integration/test_watch.py` exits 0.
6. In `clutch/docs/host-running.md`, the "Stop serve before" sentence no longer names `review`, and the verb table's `review` row says `Yes` under "Works while serve runs?".

## Verification
```
./dev.py test tests/unit/test_verdict_extension.py tests/integration/test_review_command.py tests/integration/test_control_cli.py tests/integration/test_watch.py
```

## Definition of rejected
- `review` takes `clutch.lock`.
- `review`, `confirm` or `reject` reaps while another process holds `clutch.lock`.
- `confirm` or `reject` publishes an admission request after intake refused the stem or the commit lock timed out.
- `view.js` computes availability or parses the lock strings.
- `triage`, `dismiss` or `migrate-box` move off the engine lock.

## Time budget
- expected: 60m
- stuck: 120m
