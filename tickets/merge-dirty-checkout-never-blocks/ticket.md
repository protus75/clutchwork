---
state: confirmed
source: human
priority: P0
kind: bug
---

## Depends on
none

## Context
- clutch/merge.py
- tests/unit/test_merge_dirty.py
- tickets/merge-dirty-checkout-never-blocks/evidence/ev5.txt

## Goal / Why
The owner keeps uncommitted local edits in `config.yaml` (routing, scheduler, their own tuning). Today the merge gate's `dirty_checkout` finding rejects a ticket that changes `config.yaml` while that edit exists: on 2026-11-21 `review-cost-sonnet-instance` passed Implement, Check and Review and then went to the Reject queue for it. An edit the owner makes to `config.yaml` must never affect whether a ticket merges.

After this ticket `config.yaml` is exempt from the `dirty_checkout` finding, and the squash keeps the owner's working copy: after the merge, `config.yaml` in the checkout holds the owner's local edit applied on top of the merged file, and where both changed the same lines the owner's lines win. Every other path keeps today's `dirty_checkout` behavior.

## Boundary contract
### Main-checkout local config edits at merge
- disposition: extend
- owner: clutch/merge.py (`dirty_overlap`, `write_squash`)
- consumers: the merge queue's admission for `serve`, `drain` and `run`
- observable change: a dirty `config.yaml` neither refuses nor delays a merge and survives it
- compatibility: dirty and staged checks for every other path, the squash commit contents and ordering stay as today
- acceptance: criteria 1 to 3
- tests: tests/unit/test_merge_config_local.py and tests/integration/test_merge_config_local.py
- post-merge source of truth: clutch/merge.py

## Scope in / Scope out
Scope in: in `clutch/merge.py` make `dirty_overlap` ignore `config.yaml`, and have the squash save the owner's working `config.yaml`, restore it to HEAD before `merge_squash`, then reapply the owner's edit on top of the merged file (a 3-way merge, owner's lines winning on conflict). The implementer reads `write_squash` and `Git.merge_squash` and names in the run record the simpler approach rejected. `write_squash` calls `ctx.git.status_porcelain` to learn whether `config.yaml` is dirty, and only then `_run` for `show`, `checkout` and `merge-file`. The stand-in in `tests/unit/test_merge_index_hook.py` gets `status_porcelain=AsyncMock(return_value='')` and nothing else. New tests start with a `clutch:meta` header created by `uv run clutch meta refresh <file>` with only `purpose` edited: `tests/unit/test_merge_config_local.py`, `tests/integration/test_merge_config_local.py`, and the reproducer `tests/regress_merge_config_local.py`.

Scope out: every other path's dirty check, the merge queue, runner, diagnosis, docs, and `config.yaml` itself.

## Scope fence
- clutch/merge.py
- tests/unit/test_merge_dirty.py
- tests/unit/test_merge_index_hook.py
- tests/unit/test_merge_config_local.py
- tests/integration/test_merge_config_local.py
- tests/regress_merge_config_local.py

## Acceptance criteria
1. `./dev.py test tests/integration/test_merge_config_local.py` shows a reviewed ticket that changes `config.yaml` merges while the main checkout has an uncommitted edit to `config.yaml`: the merge commit has the ticket's change and the checkout's `config.yaml` afterwards holds both the ticket's change and the owner's edit.
2. `./dev.py test tests/unit/test_merge_config_local.py` runs the new `write_squash` save, restore and 3-way-reapply lines with a fake `ctx.git` and a `tmp_path` working copy (owner's lines win on conflict; no edit means no change), and `dirty_overlap` ignores `config.yaml`. The integration test shows a ticket that does not touch `config.yaml` merges and leaves the owner's edit unchanged, and a dirty other path (`clutch/thing.py`) still refuses with `dirty_checkout`; `./dev.py test tests/unit/test_merge_dirty.py tests/unit/test_merge_config_local.py` passes.
3. `uv run python tests/regress_merge_config_local.py` prints `{"regression_result": "pass"}` and exits 0 on the fixed branch and `{"regression_result": "defect"}` with a non-zero exit on the merge base; `uv run clutch meta check tests/unit/test_merge_config_local.py tests/integration/test_merge_config_local.py tests/regress_merge_config_local.py` exits 0.

## Verification
```
./dev.py test tests/unit/test_merge_config_local.py tests/integration/test_merge_config_local.py tests/unit/test_merge_dirty.py tests/integration/test_merge.py tests/integration/test_mergequeue.py
```

## Definition of rejected
A dirty `config.yaml` that still refuses or rejects a ticket; the owner's edit lost or overwritten; any other path's dirty check weakened; a regression reproducer passing on the merge base; a test added to `tests/integration/test_merge.py` or `tests/integration/test_mergequeue.py`.

## Time budget
- expected: 25m
- stuck: 50m

## Regression
```
uv run python tests/regress_merge_config_local.py
```
- carries: tests/regress_merge_config_local.py
