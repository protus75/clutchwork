---
state: draft
source: human
priority: P0
kind: feature
---

## Depends on
- snapshot-from-duckdb-cache

## Context
- clutch/observe.py::snapshot
- clutch/config.py::Config
- clutch/config.py::Count
- clutch/docs/host-contract.md#Complete field inventory
- tests/integration/test_host_contract.py::inventory
- tests/integration/test_host_contract.py::test_host_contract_schema_coverage
- clutch/help.py
- docs/how-clutch-works.md#11. Config
- docs/how-clutch-works.md#2.1 Verbs
- tickets/snapshot-from-duckdb-cache/ticket.md

## On-demand
- clutch/__main__.py
- clutch/docs/host-running.md
- tests/unit/test_main_view_group.py

## Goal / Why
Owner design, 2026-11-19. `clutch view snapshot` emits one row for every merged ticket ever, about 650 on this checkout, and the number grows with every merge. Merged tickets are static history, and the extension's refresh should not reload all of it on every call. `snapshot-from-duckdb-cache` builds the snapshot's journal facts once per call; this ticket bounds how much merged history each refresh loads.

When done, a new top-level config field `snapshot_merged_limit` (default 100) caps the merged section of `clutch view snapshot` at the most recently settled N tickets. Older merged tickets are never loaded: no row, menu input, commit lookup or detail is built for them. They are loaded only when asked for explicitly with `clutch view snapshot --all-merged`. Every other part of the snapshot is unchanged, except references to an omitted merged stem, which drop the same way references to any stem without a row drop today.

## Boundary contract
### Snapshot merged-history cap
- disposition: extend
- owner: clutch/observe.py
- consumers: `clutch view snapshot` (`clutch/__main__.py`), `clutch prompt drafts`, the VS Code extension's refresh
- observable change: `observe.snapshot(ctx, *, merged_limit: int | None = None)`. With an integer, only the first `merged_limit` stems of today's newest-settled-first `merged` list become merged rows, and the omitted stems are left out of `ticket_menu_inputs`, `base` and the commit lookup. With `None`, every merged ticket is included, which is today's output. Rows, `counts["merged"]`, `depends` filtering (to stems with a row), the `Depends on` detail lines and graph lanes follow from the shown rows exactly as today.
- compatibility: callers that pass no `merged_limit` (`clutch prompt drafts`, existing tests) get today's full output. The extension needs no change; it receives the capped view.
- acceptance: with a limit, merged rows are the newest N and every non-merged row's fields other than `depends`, `detail` and `graph` equal the uncapped snapshot's
- tests: tests/unit/test_snapshot_merged_cap.py, tests/integration/test_snapshot_merged_cap.py
- post-merge source of truth: clutch/observe.py

### Config field `snapshot_merged_limit`
- disposition: extend
- owner: clutch/config.py
- consumers: `clutch/__main__.py` `view snapshot`; `clutch/docs/host-contract.md` field inventory
- observable change: new top-level `Config.snapshot_merged_limit: Count = 100`. Explicit null, zero and negative values are refused like every other `Count`.
- compatibility: existing config files load unchanged and take the default
- acceptance: `tests/integration/test_host_contract.py` schema coverage passes with the new inventory row
- tests: tests/integration/test_host_contract.py, tests/integration/test_snapshot_merged_cap.py
- post-merge source of truth: clutch/config.py

### `clutch view snapshot --all-merged`
- disposition: extend
- owner: clutch/__main__.py
- consumers: operators; the extension does not pass it in this ticket
- observable change: `view snapshot` passes `merged_limit=config.snapshot_merged_limit`; with `--all-merged` it passes `None` and prints every merged ticket. The command help describes the flag and has an example.
- compatibility: `clutch view snapshot` with no flag now prints at most `snapshot_merged_limit` merged rows
- acceptance: CLI output row counts with and without the flag
- tests: tests/unit/test_main_view_group.py, tests/integration/test_snapshot_merged_cap.py
- post-merge source of truth: clutch/__main__.py

## Scope in / Scope out
Scope in:
- `clutch/config.py`: add `snapshot_merged_limit: Count = 100` to `Config`. Nothing else changes.
- `clutch/observe.py`: add the keyword-only `merged_limit` parameter to `snapshot` and slice the `merged` list before `ticket_menu_inputs` is called, as the Boundary contract states. Nothing else in `observe.py` changes.
- `clutch/__main__.py`: add `--all-merged` (`store_true`) to the `view snapshot` parser. In `handle_watch`, call `observe.snapshot(context, merged_limit=None if args.all_merged else config.snapshot_merged_limit)`. Update the `view snapshot` `_command` help (`does` names the cap and the flag) and add the example `clutch view snapshot --all-merged`. `clutch prompt drafts` is unchanged.
- `clutch/help.py`: the `section` entry's `merged` text says the section shows the most recently settled tickets, up to `snapshot_merged_limit`. Nothing else changes.
- `clutch/docs/host-contract.md`: in the `config-fields` block, add `snapshot_merged_limit: 100` to the `Config` defaults row.
- `tests/integration/test_host_contract.py`: changes only if its schema coverage fails with the new field; no expected value in it changes.
- `clutch/docs/host-running.md`: the `view snapshot` verb row names `--all-merged` and the cap.
- `docs/how-clutch-works.md`: the section 2.1 `view snapshot` row names `--all-merged` and the cap; the section 11 Config table gains a `snapshot_merged_limit` row (default 100: merged rows `view snapshot` includes unless `--all-merged` is passed). Nothing else changes.
- `tests/unit/test_main_view_group.py`: the `observe.snapshot` patch takes `(ctx, **kw)`; add assertions that `view snapshot` passes the loaded config's `snapshot_merged_limit` and that `--all-merged` passes `None`. The existing expected outputs do not change.
- `tests/regress_snapshot_latency.py` (created by `snapshot-from-duckdb-cache`): the one expectation that changes is the row-count check. A timed run now expects one row per open fixture ticket plus `min(merged, 100)` merged rows, not one row per fixture ticket. The median threshold and fixture counts stay.
- New `tests/unit/test_snapshot_merged_cap.py`: seam-patched snapshot tests, with the same fakes `tests/unit/test_menu_admission.py` uses and `journal_facts` patched to `status.admission_facts`.
- New `tests/integration/test_snapshot_merged_cap.py`: CLI tests on a git-backed fixture under `tmp_path`.

Scope out:
- `vscode-clutchwork/`: the extension keeps calling `view snapshot` with no flag; no extension command for older history is added here.
- The journal cache, facts and hold logic (`snapshot-from-duckdb-cache`); `clutch/status.py`, `clutch/drain.py`, `clutch/journalcache.py`.
- `view watch` and `queue`: the text view is not capped.

## Scope fence
- clutch/config.py
- clutch/observe.py
- clutch/__main__.py
- clutch/help.py
- clutch/docs/host-contract.md
- clutch/docs/host-running.md
- docs/how-clutch-works.md
- tests/integration/test_host_contract.py
- tests/unit/test_main_view_group.py
- tests/unit/test_snapshot_merged_cap.py
- tests/integration/test_snapshot_merged_cap.py
- tests/regress_snapshot_latency.py

## Acceptance criteria
1. `tests/unit/test_snapshot_merged_cap.py`: a fixture has 5 merged stems with distinct settle times and two open stems, one depending on the oldest merged stem. `snapshot(ctx, merged_limit=2)` has exactly the two newest merged rows, in the uncapped snapshot's order, and `counts["merged"] == 2`. Every non-merged row equals the uncapped `snapshot(ctx)` row in every field except `depends`, `detail` and `graph`, and the dependent row's `depends` no longer names the omitted stem. A cap that keeps the oldest rows, or that also drops open rows, fails it. Checked by `./dev.py test tests/unit/test_snapshot_merged_cap.py`.
2. `tests/unit/test_snapshot_merged_cap.py`: with a spy on `observe.ticket_menu_inputs` and `observe.commits`-backed rows, `snapshot(ctx, merged_limit=2)` passes `ticket_menu_inputs` no omitted merged stem, so older history is not loaded. `snapshot(ctx)` with no limit returns all 5 merged rows. Checked by `./dev.py test tests/unit/test_snapshot_merged_cap.py`.
3. `tests/integration/test_snapshot_merged_cap.py`: in a git-backed fixture with 5 merged tickets and `snapshot_merged_limit: 2` in `config.yaml`, `main(["--config", <config>, "view", "snapshot"])` prints 2 merged rows and `... "view", "snapshot", "--all-merged"` prints 5. A config without the key loads `snapshot_merged_limit == 100`, and `snapshot_merged_limit: 0` is refused with a `ConfigError` naming the key. Checked by `./dev.py test tests/integration/test_snapshot_merged_cap.py`.
4. `./dev.py test tests/integration/test_host_contract.py tests/unit/test_main_view_group.py tests/unit/test_help.py tests/integration/test_help.py tests/unit/test_main_help.py` exits 0. `test_main_view_group.py` asserts `view snapshot` passes the config limit and `--all-merged` passes `None`, so a handler that ignores the flag fails.
5. `uv run python tests/regress_snapshot_latency.py` exits 0 with `median_s` < 2.0, and run.md records its printed JSON.
6. `./dev.py test` exits 0.
7. Review checks that `clutch/docs/host-contract.md`, `clutch/docs/host-running.md` and `docs/how-clutch-works.md` sections 2.1 and 11 name `snapshot_merged_limit`, its default, and `--all-merged`.

## Verification
```
./dev.py test tests/unit/test_snapshot_merged_cap.py tests/integration/test_snapshot_merged_cap.py tests/integration/test_host_contract.py tests/unit/test_main_view_group.py tests/unit/test_help.py tests/integration/test_help.py tests/unit/test_main_help.py
uv run python tests/regress_snapshot_latency.py
./dev.py test
```

## Definition of rejected
- Any non-merged row field other than `depends`, `detail` or `graph` differs between the capped and uncapped snapshot.
- Omitted merged stems still pass through `ticket_menu_inputs`, `base` or the commit lookup.
- `snapshot_merged_limit` is undocumented in the host-contract inventory, or accepts 0 or null.
- `vscode-clutchwork/` changes, or the cap applies to `view watch`.

## Time budget
- expected: 20m
- stuck: 40m
