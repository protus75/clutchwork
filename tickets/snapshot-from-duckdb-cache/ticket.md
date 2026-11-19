---
state: confirmed
source: human
priority: P0
kind: feature
---

## Depends on
- journal-duckdb-cache
- admission-facts-precomputed

## Context
- clutch/observe.py::snapshot
- clutch/observe.py::held
- clutch/observe.py::operator_holds
- clutch/observe.py::queue
- clutch/observe.py::text_snapshot
- clutch/observe.py::ticket_menu_inputs
- clutch/observe.py::journal
- clutch/drain.py::parked_blob
- clutch/drain.py::awaiting_operator
- clutch/drain.py::PREMISE
- clutch/status.py::reject_queue
- clutch/status.py::latest_transitions
- clutch/rework.py::settled_dependencies
- clutch/reconcile.py::orphans
- clutch/box.py::Box.enqueue
- clutch/journal.py::Journal.append
- clutch/journalcache.py
- tickets/journal-duckdb-cache/ticket.md
- tickets/admission-facts-precomputed/ticket.md
- tickets/snapshot-duckdb-under-one-second/diagnosis.json
- tickets/snapshot-duckdb-under-one-second/evidence/snapshot-incident-profile.txt
- tests/integration/test_regress_scripts_guarded.py
- tests/regress_snapshot_verdict_menu_parity.py
- tests/regress_review_menu_committed_unlocked.py
- docs/how-clutch-works.md#2.1 Verbs

## On-demand
- clutch/__main__.py
- tests/unit/test_menu_admission.py
- tests/unit/test_verdict_menu_parity.py
- tests/integration/test_stale_running.py
- tests/integration/test_watch.py

## Goal / Why
Owner design, 2026-11-19. `clutch view snapshot`, the VS Code extension's refresh, takes about 40 s on this checkout; the target is under 2 s end to end. A profile of this checkout on 2026-11-19 (37.6 s) shows `row_menu` admissions at 22.8 s, `operator_holds` at 9.1 s (`drain.awaiting_operator` recomputing `reject_queue` for each of 899 stems) and `held` at 3.2 s (`drain.parked_blob` re-scanning the whole history for each of 899 stems), while reading the JSONL journal costs 0.27 s. Merged tickets are static facts; the snapshot must not re-derive ancient history per row.

`admission-facts-precomputed` makes the menu admissions take one `AdmissionFacts` value, and `journal-duckdb-cache` adds a persistent, incrementally loaded DuckDB projection of the journal. When this ticket is done, `observe.snapshot` builds its journal-derived facts exactly once per invocation: latest states and Reject-queue membership from the DuckDB cache, split-aware settled dependencies and orphaned runs from the one in-memory history. The menu inputs and both drain holds (`parked_blob`, `awaiting_operator`) use those facts, and the per-stem hold checks run only for the stems that can hold. The snapshot JSON is identical to today's for every history. A one-time latency script times the snapshot on an incident-sized fixture.

## Boundary contract
### Extension snapshot
- disposition: extend
- owner: clutch/observe.py
- consumers: `clutch view snapshot` (`clutch/__main__.py::handle_watch`), `clutch prompt drafts`, the VS Code extension's refresh in `vscode-clutchwork/extension.js`
- observable change: the JSON output is unchanged for every history, where a history is the newline-terminated events `Journal.append` writes. New side effect: each `observe.snapshot` call opens the journal cache once (`open_journal_cache(ctx.state)` from `clutch/journalcache.py`), which loads newly appended journal lines into `<state_dir>/cache/journal.duckdb` under its `flock`, and closes it before returning. Ordering: the cache and the JSONL `journal(state)` read happen in the same call. An event appended between the two reads can make one refresh disagree with itself; the next refresh converges. Likewise, an unterminated final journal line (a write still in progress) is read by `observe.journal` but not yet loaded by the cache; that one refresh may disagree with itself, and the refresh after the line's newline lands converges. Equality claims in this ticket cover newline-terminated journals only; neither reader changes here.
- compatibility: preserved output. The `view snapshot` help's `reads`/`writes` lines now name the journal cache; the journal stays the authority and deleting `cache/` loses nothing.
- acceptance: on the fixture in `tests/integration/test_snapshot_cache_facts.py`, the snapshot equals the one built from pre-change event-only derivations, and the cache is opened exactly once per call
- tests: tests/integration/test_snapshot_cache_facts.py, tests/unit/test_observe_journal_facts.py
- post-merge source of truth: clutch/observe.py for the snapshot; the JSONL journal for every fact

### Snapshot journal facts
- disposition: create
- owner: clutch/observe.py
- consumers: `observe.snapshot`; the tests that feed synthetic events to the snapshot
- observable change: new `journal_facts(state: Path, history) -> AdmissionFacts`. Inside one `with open_journal_cache(state) as cache:` it returns `AdmissionFacts(states=cache.last_states(), reject=frozenset(cache.reject_queue()), settled=settled_dependencies(history), orphans=frozenset(orphans(history)))`. It writes nothing but the cache file and its lock.
- compatibility: new function; no existing caller changes behavior
- acceptance: on newline-terminated segment files under `tmp_path`, `journal_facts(state, history)` equals `status.admission_facts(history)` for the same events
- tests: tests/unit/test_observe_journal_facts.py
- post-merge source of truth: clutch/observe.py
- closest existing: `status.admission_facts(events)` (from `admission-facts-precomputed`) folds all four facts from events and cannot read the persistent cache; `JournalCache` (from `journal-duckdb-cache`) answers states and the Reject queue but has no split-aware settled set and no orphan set
- earning reason: a storage boundary and an external-effect fake. It is the one place the snapshot touches the persistent cache file, and tests that feed synthetic events replace it with `status.admission_facts(history)` instead of building a DuckDB file.

### Observe hold and menu helpers
- disposition: replace
- owner: clutch/observe.py
- consumers: `observe.snapshot`, `observe.text_snapshot` and `observe.queue` (the `view watch` text view), and the tests that patch or call these helpers
- observable change: old contracts: `held(history, blobs)` checks every stem in `history`; `operator_holds(ctx, history)` checks every stem in `history`; `ticket_menu_inputs(ctx, history, stems, holder, interrupted)` builds `admission_facts(history)` itself. Replacements: `held(history, blobs, candidates)` and `operator_holds(ctx, history, candidates)` check only the stems in `candidates`, with the same per-stem rule (`drain.parked_blob` and `drain.awaiting_operator`) and the same config loading (caps loaded only when `candidates` is non-empty); `ticket_menu_inputs(ctx, facts, stems, holder, interrupted)` takes the prebuilt `AdmissionFacts` and builds none. `snapshot` passes `held` the stems whose `facts.states` value is `drain.PREMISE` or `gate_failed` (`parked_blob` returns a blob only when the stem's latest transition is one of these), and `operator_holds` the stems in `facts.reject` (`awaiting_operator` is false outside the Reject queue). `text_snapshot` and `queue` pass every stem in the history, as today.
- compatibility: breaking for in-repo callers only; every caller and test patch migrates in this change, with no default argument or old-signature wrapper left behind. Hold results are preserved for every history.
- acceptance: the snapshot equality and call-count criteria below; `tests/integration/test_watch.py` text-view and queue assertions pass unchanged
- tests: tests/integration/test_snapshot_cache_facts.py, tests/unit/test_observe_journal_facts.py, tests/integration/test_watch.py, tests/unit/test_menu_admission.py
- post-merge source of truth: clutch/observe.py; the hold rules stay in clutch/drain.py

## Scope in / Scope out
Scope in:
- `clutch/observe.py`:
  - Add `journal_facts` as the Boundary contract states, importing `open_journal_cache` from `clutch.journalcache`, `AdmissionFacts` from `clutch.status`, and `orphans` from `clutch.reconcile` (move today's function-local `from clutch.reconcile import orphans` in `snapshot` to wherever avoids an import cycle).
  - In `snapshot`, after `history = as_events(events)`, build `facts = journal_facts(state, history)` once. Use `facts.settled` in place of `settled_dependencies(history)`, `facts.orphans` in place of `orphans(history)`, and pass `facts` to `ticket_menu_inputs`. Compute `reject_stems = operator_holds(ctx, history, facts.reject)` and `held(history, blobs, {s for s, st in facts.states.items() if st in (PREMISE, "gate_failed")})`. Keep `last_bodies(history)` for merged rows' bodies and timestamps.
  - Change `held`, `operator_holds` and `ticket_menu_inputs` as the Boundary contract states. `ticket_menu_inputs` reads `facts.states` and puts `facts` in its row inputs; it no longer calls `admission_facts`.
  - `text_snapshot` passes `held` the set of stems in its history; `queue` passes `operator_holds` the same set. Their output does not change.
  - Any further cost found while meeting the 2 s target may be removed inside `clutch/observe.py` only, with the output unchanged; name each one in run.md.
- `clutch/__main__.py`: in the `view snapshot` `_command` help, change `writes="Nothing."` to say it updates the rebuildable journal cache under the state directory, and add the journal cache to `reads`. Nothing else in `__main__.py` changes.
- Test migrations, each keeping its expected outcomes. Every test that patches `observe.journal` (or `watch.journal`) with synthetic events and then calls `snapshot` also patches `journal_facts` with `lambda state, history: status.admission_facts(history)`. Every `held` patch takes `(history, blobs, candidates)` and every `operator_holds` patch takes `(ctx, history, candidates)`:
  - `tests/unit/test_menu_admission.py`: the snapshot test that patches `journal` adds the `journal_facts` patch; the direct `observe.ticket_menu_inputs(ctx, history, ...)` call passes `status.admission_facts(history)`; `fake_snapshot_inputs` names its second parameter `facts`.
  - `tests/unit/test_verdict_menu_parity.py`, `tests/integration/test_stale_running.py`, `tests/regress_snapshot_verdict_menu_parity.py` and `tests/regress_review_menu_committed_unlocked.py`: the same patch migration.
  - `tests/integration/test_watch.py`: the same patch migration in the snapshot tests that patch `watch.journal`, `watch.held` or `watch.operator_holds` (today lines near 296, 367-369, 424, 453, 480, 664 and 700). One assertion changes: in `test_observe_verbs_take_no_lock_and_write_nothing` (today lines 204-222), the `before`/`after` comparisons leave out files under the state directory's `cache/` (the rebuildable `journal.duckdb` and its lock), so `after == before` still checks every other state file, and the lock and stdout assertions stay as they are. No other assertion changes, and no new test goes in this file.
  - `tests/unit/test_admission_facts.py` (created by `admission-facts-precomputed`): the one expectation that changes is that `ticket_menu_inputs` builds facts once. It now calls `status.admission_facts` zero times and passes the given `facts` object to every row. Nothing else in that file changes.
- New `tests/unit/test_observe_journal_facts.py` (disk only under `tmp_path`): `journal_facts` equality against `status.admission_facts`, and `held`/`operator_holds` checking only their candidates.
- New `tests/integration/test_snapshot_cache_facts.py`: a small git-backed fixture under `tmp_path` and the equality and call-count criteria below. It carries in the test file a reference copy of today's event-only derivations: facts from `status.admission_facts(history)`, `held` over every stem in the history, and `operator_holds` over every stem in the history.
- New `tests/snapshot_scale_fixture.py` (not collected: no `test_` prefix), with `build(root: Path) -> dict` that writes an incident-sized host under `root` and returns its counts:
  - a git repository with a `config.yaml` loaded by `clutch.config.load_config` (state dir `.clutch`; copy the shape of a config an existing integration test writes) and 694 committed `tickets/<stem>/ticket.md` files;
  - at least 640 stems whose latest transition is `merged` with a `commit` naming a real commit on `main` (one commit per merged stem; `git fast-import` is acceptable for speed);
  - the rest open: drafts, confirmed tickets with depends, one Reject-queue stem, one premise park whose run sha equals its committed blob, and one orphaned `running` stem. Open tickets parse with `parse_ticket`, so no row is invalid;
  - at least 37,763 journal events, written through `clutch.journal.Journal.append` or as newline-terminated segment lines in exactly the envelope it writes, so `Journal.read()` returns them all;
  - at least 791 Suggestion Box messages written through `clutch.box.Box.enqueue`.
- New `tests/regress_snapshot_latency.py` with an `if __name__ == "__main__":` guard and no output on import. It builds the fixture in a temporary directory and refuses (exit 2, `{"error": ...}` on stdout) when a count is below the thresholds above. It runs one untimed warm-up `[sys.executable, "-m", "clutch", "view", "snapshot"]` with `cwd` at the fixture and `PYTHONPATH` at this repo root; the warm-up builds the cache, as the extension's first refresh does. It then times three fresh processes with `time.perf_counter`, each of which must exit 0 and print JSON with one row per fixture ticket and one box row per message. It prints one JSON object with `cold_s`, `timings_s`, `median_s`, `events`, `tickets` and `box`, and exits 0 only when `median_s < 2.0`. It is a one-time check run in `## Verification`; no standing pytest timing gate is added.
- `docs/how-clutch-works.md`: in section 2.1, the `view snapshot` row says the snapshot refreshes the journal cache. In the extension paragraph, the sentence beginning "`clutch view snapshot` builds its data read-only" says the snapshot builds its journal facts once per call from the journal cache and the in-memory history, and checks the drain's holds only for stems that can hold. Nothing else in that file changes.
- run.md records the latency script's printed JSON and each hot spot removed.

Scope out:
- The merged-history cap, its config field and any `view snapshot` flag: `snapshot-merged-history-cap`.
- `clutch/journalcache.py`, `clutch/journal.py`, `clutch/status.py`, `clutch/drain.py`, `clutch/rework.py`, `clutch/reconcile.py` and the scheduler or serve code: the hold and admission rules and both journal readers do not change. How the journal reader and the cache treat an unterminated final line is not reconciled here.
- `vscode-clutchwork/` and `clutch/help.py`: no new extension surface or vocabulary.
- `tests/regress_engine_flag_only_drain_serve.py`: it patches no journal-derived seam, and its temporary state directory takes a real cache.
- The other hot test files; no new test goes into `tests/integration/test_watch.py`.

## Scope fence
- clutch/observe.py
- clutch/__main__.py
- docs/how-clutch-works.md
- tests/unit/test_menu_admission.py
- tests/unit/test_verdict_menu_parity.py
- tests/unit/test_admission_facts.py
- tests/unit/test_observe_journal_facts.py
- tests/integration/test_stale_running.py
- tests/integration/test_watch.py
- tests/integration/test_snapshot_cache_facts.py
- tests/regress_snapshot_verdict_menu_parity.py
- tests/regress_review_menu_committed_unlocked.py
- tests/snapshot_scale_fixture.py
- tests/regress_snapshot_latency.py

## Acceptance criteria
1. `tests/unit/test_observe_journal_facts.py`: for histories written as newline-terminated journal segments under `tmp_path` (through `Journal.append` or its exact envelope), `journal_facts(state, history)` equals `status.admission_facts(history)` field by field. The histories are empty; merged; rejected; an orphaned `running` stem; a `routed: reject_queue` terminal; and a split whose leaves all settled. A `journal_facts` that uses the cache's non-split `settled()` fails on the split history, and one that leaves out the cache's Reject queue fails on the routed history. Checked by `./dev.py test tests/unit/test_observe_journal_facts.py`.
2. `tests/unit/test_observe_journal_facts.py`: with `drain.parked_blob` and `drain.awaiting_operator` wrapped with counters, `held(history, blobs, {"a"})` and `operator_holds(ctx, history, {"a"})` call their rule only for `"a"`, even when the history names other stems. `operator_holds` with empty candidates returns `set()` without loading config: a nonexistent `ctx.config` path does not raise. Checked by `./dev.py test tests/unit/test_observe_journal_facts.py`.
3. `tests/integration/test_snapshot_cache_facts.py` builds a git-backed fixture under `tmp_path` with a newline-terminated journal. Its history yields at least one row each with status key `merged`, `held_change`, `held_operator` (one `ticket_changed` and one cap-spent Reject-queue stem), `interrupted`, `waits_on` and `draft`, plus a split whose superseded stem's dependent is queued. With `observe.datetime` frozen, `observe.snapshot(ctx)` equals, as parsed JSON, the snapshot built with `journal_facts`, `held` and `operator_holds` patched to the reference event-only derivations over every stem. A snapshot that drops a premise park or a cap-spent hold fails it. Checked by `./dev.py test tests/integration/test_snapshot_cache_facts.py`.
4. `tests/integration/test_snapshot_cache_facts.py`: on the same fixture, one `observe.snapshot(ctx)` call opens `open_journal_cache` exactly once. It calls `drain.awaiting_operator` once per Reject-queue stem and `drain.parked_blob` once per stem whose latest state is `premise_failed` or `gate_failed`, not once per stem in the history. A snapshot that rebuilds facts per row or checks holds for every stem fails it. Checked by `./dev.py test tests/integration/test_snapshot_cache_facts.py`.
5. The migrated tests pass with unchanged expected outcomes, except that `test_observe_verbs_take_no_lock_and_write_nothing` leaves out files under the state directory's `cache/` from its before/after comparison and still checks every other state file: `./dev.py test tests/unit/test_menu_admission.py tests/unit/test_verdict_menu_parity.py tests/unit/test_admission_facts.py tests/integration/test_stale_running.py tests/integration/test_watch.py tests/integration/test_menu_verb_parity.py tests/integration/test_regress_scripts_guarded.py` exits 0, and `uv run python tests/regress_snapshot_verdict_menu_parity.py` and `uv run python tests/regress_review_menu_committed_unlocked.py` each print `{"regression_result": "pass"}`.
6. `uv run python tests/regress_snapshot_latency.py` exits 0. It prints `events` >= 37763, `tickets` >= 694, `box` >= 791 and `median_s` < 2.0 over three timed fresh `clutch view snapshot` processes. run.md records the printed JSON.
7. `./dev.py test` exits 0, and `uv run clutch view snapshot --help` names the journal cache in its writes line.
8. Review checks that `docs/how-clutch-works.md` section 2.1 and the extension paragraph describe the cache-built facts, and that `git diff` leaves `clutch/status.py`, `clutch/drain.py`, `clutch/journal.py` and `clutch/journalcache.py` unchanged.

## Verification
```
./dev.py test tests/unit/test_observe_journal_facts.py tests/integration/test_snapshot_cache_facts.py tests/unit/test_menu_admission.py tests/unit/test_verdict_menu_parity.py tests/unit/test_admission_facts.py tests/integration/test_stale_running.py tests/integration/test_watch.py tests/integration/test_menu_verb_parity.py tests/integration/test_regress_scripts_guarded.py
uv run python tests/regress_snapshot_verdict_menu_parity.py
uv run python tests/regress_review_menu_committed_unlocked.py
uv run python tests/regress_snapshot_latency.py
./dev.py test
```

## Definition of rejected
- Any snapshot JSON field differs from the event-only reference on the criterion 3 fixture, or an existing test's expected outcome changes other than the `cache/` exclusion in `test_observe_verbs_take_no_lock_and_write_nothing`.
- That test's comparison leaves out any state file outside `cache/`.
- The snapshot opens the journal cache more than once per call, or derives states or Reject-queue membership by re-scanning the history once per row or per stem.
- `clutch/status.py`, `clutch/drain.py`, `clutch/journal.py` or `clutch/journalcache.py` changes, or a hold rule is copied into `observe.py` instead of called.
- An old-signature wrapper, default argument or events-accepting path remains for `held`, `operator_holds` or `ticket_menu_inputs`.
- The latency median is 2.0 s or more, the fixture counts fall below the thresholds, or a pytest timing gate is added.
- A new test goes into `tests/integration/test_watch.py`.

## Time budget
- expected: 30m
- stuck: 60m