---
state: draft
source: human
priority: P0
kind: chore
---

## Depends on
- none

## Context
- clutch/status.py
- clutch/observe.py::MenuEntry
- clutch/observe.py::MENU
- clutch/observe.py::row_menu
- clutch/observe.py::ticket_menu_inputs
- clutch/__main__.py::_review
- clutch/__main__.py::_lint
- clutch/__main__.py::_order
- clutch/runner.py::verdict_locked
- clutch/runner.py::_admit
- clutch/rework.py::settled_dependencies
- clutch/rework.py::supersedes_maps
- clutch/reconcile.py::orphans
- tests/unit/test_menu_admission.py
- tests/unit/test_paved_roads.py
- tests/integration/test_menu_verb_parity.py::verb_inputs
- tickets/snapshot-duckdb-under-one-second/evidence/snapshot-incident-profile.txt
- tickets/snapshot-duckdb-under-one-second/diagnosis.json

## Goal / Why
`clutch view snapshot` takes about 40 s on this repo's journal. The profile in `tickets/snapshot-duckdb-under-one-second/evidence/snapshot-incident-profile.txt` (owner-requested fix, 2026-11-19) shows 31.5 s of a 31.5 s run inside `observe.snapshot`, of which 19.7 s is `row_menu`: 4,809 `last_states` calls (13.4 s), 1,572 `reject_queue` calls (12.8 s) and 4,810 `latest_transitions` calls (12.0 s). Every menu admission in `clutch/status.py` takes the whole event list and re-derives the latest state per stem, settled dependencies, orphaned runs, or Reject-queue membership on each call, so one snapshot re-scans about 37,000 events for each of 694 rows and each menu key.

When done, those facts are computed once from the events into one `AdmissionFacts` value, and every admission function takes that value instead of events. The snapshot menu builds the facts once per `ticket_menu_inputs` call; each CLI verb builds them once per command. Every admission outcome, message and paved road is identical to today for every history. This is child 1 of the split recorded in `tickets/snapshot-duckdb-under-one-second/diagnosis.json`; the DuckDB cache and the snapshot rewiring of `operator_holds`/`parked_blob` are later tickets.

## Boundary contract
### Admission facts
- disposition: create
- owner: clutch/status.py
- consumers: the status admission functions, `clutch/observe.py::ticket_menu_inputs` (snapshot menus), `clutch/__main__.py` `_review`, `_lint` and `_order`, `clutch/runner.py` `verdict_locked` and `_admit`
- observable change: new frozen dataclass `AdmissionFacts` with fields `states: Mapping[str, str]` (equal to `last_states(events)`), `settled: frozenset[str]` (equal to `rework.settled_dependencies(events)`), `orphans: frozenset[str]` (equal to `frozenset(reconcile.orphans(events))`) and `reject: frozenset[str]` (equal to `frozenset(reject_queue(events))`), built by `admission_facts(events: Iterable[Event]) -> AdmissionFacts`, which reads its iterable once (materialized as a tuple) and is pure: no I/O, no clock, no journal write
- compatibility: `last_states`, `latest_transitions`, `reject_queue`, `settled_dependencies` and `orphans` keep their signatures and results; no persisted format changes
- acceptance: on each representative history in the new test file, every field equals the existing function it names
- tests: tests/unit/test_admission_facts.py
- post-merge source of truth: clutch/status.py
- closest existing: `Status` in `clutch/status.py` is a rendered projection with closed rows only and no settled-dependency or orphan sets; `last_states` and `reject_queue` each return one fact and are what is recomputed today; `rework.settled_dependencies` and `reconcile.orphans` each scan the full history per call
- earning reason: multiple production consumers (the snapshot menu in `observe.py`, three `__main__.py` verbs and two `runner.py` verbs) share the same four facts, and the incident profile shows per-call recomputation costs 19.7 s of a 31.5 s snapshot

### Status admission functions
- disposition: replace
- owner: clutch/status.py
- consumers: `clutch/observe.py` `MENU` input names and `ticket_menu_inputs`, `clutch/__main__.py` `_review`, `_lint`, `_order`, `clutch/runner.py` `verdict_locked`, `_admit`, and the tests that call them
- observable change: old contract: `run_admission(stem, events, ...)`, `review_admission(stem, events, ...)`, `order_admission(stem, events, ...)`, `lint_admission(stem, events, ...)`, `verdict_refusal(events, stem, kill, draft, interrupted)`, `confirm_admission(events, stem, draft, interrupted)`, `reject_admission(events, stem, draft, interrupted)`. Replacement: the `events` parameter becomes `facts: AdmissionFacts` in the same position with every other parameter unchanged. The functions read `facts.states`, `facts.settled`, `facts.orphans` and `facts.reject` and never call `last_states`, `reject_queue`, `settled_dependencies` or `orphans`. `verdict_refusal` applies `interrupted` as an overlay: a stem in `interrupted` has last state `abandoned` and is not in the Reject queue, exactly as appending an `abandoned` transition for it did. Outcomes, messages and paved roads are preserved for every input.
- compatibility: breaking for in-repo callers only; every caller and the `MENU` input tuples migrate in this change, with no shim or events-accepting variant left behind
- acceptance: equality tests show each new admission returns the same `Admission` (or refusal tuple) as the pre-change event-based rule on representative histories, and the admissions run with `last_states` and `reject_queue` patched to raise
- tests: tests/unit/test_admission_facts.py, tests/unit/test_menu_admission.py, tests/unit/test_paved_roads.py, tests/integration/test_menu_verb_parity.py
- post-merge source of truth: clutch/status.py

## Scope in / Scope out
Scope in:
- `clutch/status.py`: add `AdmissionFacts` and `admission_facts(events)` as the Boundary contract states, importing `settled_dependencies` and `orphans` lazily inside `admission_facts` the way the admissions do today (avoids import cycles). Change `run_admission`, `review_admission`, `order_admission`, `lint_admission`, `verdict_refusal`, `confirm_admission` and `reject_admission` to take `facts` in place of `events`, reading `facts.states.get(stem)`, `facts.settled`, `stem in facts.orphans` and `stem in facts.reject`. `verdict_refusal` drops its `SimpleNamespace` history rebuild and applies `interrupted` as the overlay above; drop the `SimpleNamespace` import if nothing else uses it. `project` and `render` are unchanged.
- `clutch/observe.py`: in the `MENU` table, rename the input name `events` to `facts` in the review, lint, run, confirm, reject, priority and runs-before entries. In `ticket_menu_inputs`, build `facts = admission_facts(history)` once before the stem loop, use `facts.states` in place of its own `last_states(history)` call, and put `facts=facts` in the `common` dict in place of `events=history`. Add the import. Nothing else in `observe.py` changes: `snapshot`, `operator_holds`, `held`, `row_menu` and the drain holds stay as they are.
- `clutch/__main__.py`: `_review` builds facts once from its history (`admission_facts(())` for the first, pre-read call) and passes them to all three `review_admission` calls; `_lint` builds facts once from `events` before the stem loop; `_order` builds facts once from `events`, takes `state` from `facts.states` and the orphan test from `facts.orphans`, and passes facts to both `order_admission` calls. Update the `clutch.status` import line.
- `clutch/runner.py`: `verdict_locked` passes `admission_facts(history)` to `verdict_refusal`; `_admit` passes `admission_facts(history)` to `run_admission`. Update the `clutch.status` import line.
- `tests/unit/test_menu_admission.py`: the direct `status.order_admission`, `status.lint_admission`, `run_admission`/`review_admission` calls (in `test_stem_admissions`, `test_run_review_admission`, `test_dispatch_verbs_use_admission_refusals`) pass `status.admission_facts(<the same events>)` in place of the event list; expected outcomes and messages do not change.
- `tests/unit/test_paved_roads.py`: the `run_admission("item", [], False, None)` call passes `admission_facts([])`; the expected paved road does not change.
- `tests/integration/test_menu_verb_parity.py` `verb_inputs`: `events=history` becomes `facts=status.admission_facts(history)`; nothing else changes.
- New `tests/unit/test_admission_facts.py` covering the criteria below with in-memory events (`SimpleNamespace` events as `tests/unit/test_menu_admission.py::event` builds them), no repo files. Its old-vs-new equality pins carry a small reference copy of the pre-change event-based rules (from `clutch/status.py` at the base commit) in the test file and compare outcomes on each history.

Scope out: DuckDB or any new dependency; `clutch/journal.py`; `observe.snapshot` and `operator_holds`/`held`/`clutch/drain.py` `parked_blob`/`awaiting_operator` (later child tickets of `snapshot-duckdb-under-one-second`); `clutch/drain.py` and serve code; `project`/`render`; any snapshot latency target or timing test; `tests/unit/test_verdict_menu_parity.py`, `tests/integration/test_watch.py` and the `tests/regress_*.py` files, which do not call the changed signatures; the hot integration test files.

## Scope fence
- clutch/status.py
- clutch/observe.py
- clutch/__main__.py
- clutch/runner.py
- tests/unit/test_menu_admission.py
- tests/unit/test_paved_roads.py
- tests/integration/test_menu_verb_parity.py
- tests/unit/test_admission_facts.py

## Acceptance criteria
1. For each representative history in `tests/unit/test_admission_facts.py` (empty; one stem merged; one running with no terminal, i.e. an orphan; one rejected; one routed `reject_queue`; one `reject_arrival` after a terminal; one `reject_verdict` clearing the queue; one routed to the queue then merged; one split whose `supersedes` leaves all settled and one whose leaf is still open), `admission_facts(h)` has `states == last_states(h)`, `settled == settled_dependencies(h)`, `orphans == frozenset(orphans(h))` and `reject == frozenset(reject_queue(h))`; a facts builder that skips `reject_arrival` or keeps a merged stem in `reject` fails it. Checked by `./dev.py test tests/unit/test_admission_facts.py`.
2. For every history in criterion 1, every stem in it plus one absent stem, and every combination of `kill`, `draft` and `interrupted` in {empty, {that stem}}, `verdict_refusal(admission_facts(h), stem, kill, draft, interrupted)` equals the reference pre-change rule run on `h`; an implementation that ignores `interrupted` (so an interrupted running stem is refused as `is running`) fails it. Checked by `./dev.py test tests/unit/test_admission_facts.py`.
3. For every history in criterion 1, `run_admission`, `review_admission`, `order_admission` (with `lock_holder` None and non-None) and `lint_admission` given `admission_facts(h)` return an `Admission` equal to the reference pre-change rule on `h`, including a running orphan with `lock_holder=None` admitting to order and a run whose dependency's split leaves are unsettled refusing with `depends on unmerged`. Checked by `./dev.py test tests/unit/test_admission_facts.py`.
4. With `clutch.status.last_states`, `clutch.status.reject_queue`, `clutch.rework.settled_dependencies` and `clutch.reconcile.orphans` monkeypatched to raise, calling each of the seven admission functions with a prebuilt `AdmissionFacts` returns an `Admission` or refusal tuple, not an exception. Checked by `./dev.py test tests/unit/test_admission_facts.py`.
5. `observe.ticket_menu_inputs` called for 3 stems (with the fakes `tests/unit/test_menu_admission.py::test_snapshot_reads_one_porcelain_and_shared_graphs` uses, with a spy wrapping `observe.admission_facts`, the name `observe.py` imports) calls it exactly once, not once per stem or menu key, and every ticket row's inputs carry the same `facts` object under `facts` with no `events` key. Checked by `./dev.py test tests/unit/test_admission_facts.py`.
6. The existing menu and verb parity tests pass with unchanged expected outcomes: `./dev.py test tests/unit/test_menu_admission.py tests/unit/test_paved_roads.py tests/unit/test_verdict_menu_parity.py tests/integration/test_menu_verb_parity.py` exits 0.
7. No `clutch/` source passes events to the changed admissions: `grep -rnE "(run|review|order|lint|confirm|reject)_admission\(|verdict_refusal\(" clutch/` shows only `facts`-taking calls, and the full suite `./dev.py test` exits 0.

## Verification
```
./dev.py test tests/unit/test_admission_facts.py tests/unit/test_menu_admission.py tests/unit/test_paved_roads.py tests/unit/test_verdict_menu_parity.py tests/integration/test_menu_verb_parity.py
./dev.py test
```

## Definition of rejected
- Any admission outcome, message or paved road changes for an existing test or for a criterion-1 history.
- An admission function still accepts events, or an events-accepting wrapper, shim or dual path remains.
- The change touches `observe.snapshot`, `operator_holds`, `clutch/drain.py`, `clutch/journal.py`, adds DuckDB or any dependency, or edits a hot test file.
- The equality tests compare the new code against itself rather than against the pre-change event-based rules.

## Time budget
- expected: 25m
- stuck: 50m
