---
state: draft
source: human
priority: P0
kind: feature
---

## Depends on
- none

## Context
- clutch/runner.py::Checkout
- clutch/roadmap.py::_write_row
- clutch/roadmap.py::drive
- clutch/author.py::author
- clutch/author.py::commit_record
- tests/unit/test_roadmap_drive.py

## On-demand
- tests/unit/test_roadmap_author.py
- tests/unit/test_author_calibration.py
- tests/unit/test_author_roadmap_row.py
- tests/unit/test_author_decline_findings.py
- tests/unit/test_author_stem_claimed.py
- tests/unit/test_closed_sets_remaining.py
- tests/integration/test_roadmap_ship.py
- tests/integration/test_roadmap_named_stem.py
- tests/integration/test_roadmap_refile.py

## Goal / Why
Every main-checkout write the roadmap driver makes holds one in-process lock, `Checkout.main_writes`, so the follow-up tickets `driver-pass-overlaps-dispatch` (drain) and `serve-driver-overlaps-dispatch` (serve) can run the driver pass concurrently with a ticket run and serialize only those writes against merge admission and ticket intake. Today the whole driver pass (Author and requisition-review LLM calls, roadmap row commits, `ship`) is serialized against dispatch: drain runs it inline after every settle (`clutch/drain.py` `run` -> `_run_driver`) and serve refuses admission while `driver_pending()` holds and runs it under the exclusive `mutations()` gate. On 2026-11-19 `graphics-kind` was authored and requisition-reviewed by the driver while the confirmed tickets `document-agent-roadmap-prompt`, `graphics-kind` and `conflict-rerun-accounting` waited; the owner requires authoring to overlap implementation. This ticket adds only the lock and makes the driver-side writers hold it; nothing runs concurrently yet, so behavior is unchanged.

## Boundary contract
### Checkout main-checkout write gate
- disposition: extend
- owner: clutch/runner.py
- consumers: clutch/roadmap.py, clutch/author.py, and after the follow-ups clutch/drain.py, clutch/runner.py `drive`, clutch/serve.py
- observable change: `Checkout` gains a field `main_writes: asyncio.Lock` with `field(default_factory=asyncio.Lock, compare=False, repr=False)`; `dataclasses.replace(checkout, ...)` copies share the same lock object, so every copy an engine derives (config snapshots, the driver's checkout, pipeline preparation) holds one lock
- compatibility: every existing `Checkout(...)` construction stays valid; Checkout equality and repr are unchanged
- acceptance: `replace(checkout, config=x).main_writes is checkout.main_writes`
- tests: tests/unit/test_main_write_gate.py
- post-merge source of truth: clutch/runner.py::Checkout

### Driver-side main-checkout writers
- disposition: extend
- owner: clutch/roadmap.py and clutch/author.py
- consumers: `roadmap.drive` (via `clutch/__main__.py` `build_driver`), `clutch roadmap author`, triage passes (`clutch/triage.py`) that author tickets or write decision records
- observable change: these sections run inside `async with checkout.main_writes:` -- (1) `roadmap._write_row`, from its re-read of `docs/roadmap.md` through its commit; (2) the `ship(checkout)` action inside `roadmap.drive` (whole release gate, bump, tag, publish, packages); (3) in `author.author`, the block from the "stem was claimed since the gate check" existence check through the ticket-file write, the `ticket-plane/<stem>/author` commit effect, and its failure restore; (4) the `git.commit` inside `author.commit_record`'s effect. The Author and requisition-review LLM calls, the gate's evidence copies, journal appends and Box writes stay outside the lock
- compatibility: outputs, commit messages, journal events, refusals and failure handling are unchanged; with no concurrent holder the lock is uncontended. The lock is never acquired while held: none of the four sections calls another
- acceptance: each of the four sections observes `checkout.main_writes.locked()` at its commit, and the LLM call does not
- tests: tests/unit/test_main_write_gate.py
- post-merge source of truth: clutch/roadmap.py, clutch/author.py

## Scope in / Scope out
Scope in:
- `clutch/runner.py`: add the `main_writes` field to `Checkout` as declared (import `field` from `dataclasses`). Nothing else in runner.py changes.
- `clutch/roadmap.py`: hold `checkout.main_writes` across the whole body of `_write_row`, and around the `ship(checkout)` call in `drive` (wrap the call inside the lambda's action, for example `async def shipped(): async with checkout.main_writes: return await ship(checkout)`), keeping the `Refusal` handling as it is.
- `clutch/author.py`: hold `checkout.main_writes` across the block in `author` that starts at the `if (checkout.repo / path).exists() and reply.stem not in author_gate.copied:` check and ends after the `try/except` that writes the ticket file, runs the commit effect and restores on failure (the `failure_declined` call on a commit failure may stay inside or move just after; it must not re-acquire the lock while held, because `commit_record` acquires it). Hold it around the `git.commit` call inside `commit_record`'s `commit()` closure.
- Test fakes: unit and integration tests that build a `SimpleNamespace` checkout and reach a gated section now need a `main_writes=asyncio.Lock()` attribute. Add only that attribute to the fakes in the fenced test files whose tests fail without it; change nothing else in them.
- New `tests/unit/test_main_write_gate.py` covering every acceptance criterion with fakes and `tmp_path` only.

Scope out: running the driver concurrently with dispatch (`driver-pass-overlaps-dispatch` for drain, `serve-driver-overlaps-dispatch` for serve), the merge and intake holders of the lock (those follow-ups add them), `StageContext`, `clutch/drain.py`, `clutch/serve.py`, `clutch/triage.py`, and documentation (the follow-ups update the how-clutch-works guide when behavior changes).

## Scope fence
- clutch/runner.py
- clutch/roadmap.py
- clutch/author.py
- tests/unit/test_main_write_gate.py
- tests/unit/test_roadmap_drive.py
- tests/unit/test_roadmap_author.py
- tests/unit/test_author_calibration.py
- tests/unit/test_author_roadmap_row.py
- tests/unit/test_author_decline_findings.py
- tests/unit/test_author_stem_claimed.py
- tests/unit/test_closed_sets_remaining.py
- tests/integration/test_roadmap_ship.py
- tests/integration/test_roadmap_named_stem.py
- tests/integration/test_roadmap_refile.py

## Acceptance criteria
1. `tests/unit/test_main_write_gate.py` asserts that a `runner.Checkout` and `dataclasses.replace(checkout, config=other)` share one lock (`is`, not merely equal), and that two separately constructed Checkouts with equal fields still compare equal; checked by `./dev.py test tests/unit/test_main_write_gate.py`.
2. The same file drives `roadmap._write_row` with a fake git whose `commit` records `checkout.main_writes.locked()` and asserts it recorded `True`, not `False`; and drives `roadmap.drive` with `ship` monkeypatched to record `checkout.main_writes.locked()` and asserts `True`, while the `author_messages` callback passed to `drive` records `False` (the Author call is outside the lock).
3. The same file drives `author.commit_record` with a fake git whose `commit` records `checkout.main_writes.locked()` and asserts `True`; and drives `author.author` through a successful commit with a fake driver whose `run` (the LLM call) records `locked()` as `False` and whose commit effect records it as `True`.
4. The full suite passes with the fakes updated: `./dev.py test`.

## Verification
```
./dev.py test tests/unit/test_main_write_gate.py tests/unit/test_roadmap_drive.py tests/unit/test_roadmap_author.py tests/unit/test_author_calibration.py tests/unit/test_author_roadmap_row.py tests/unit/test_author_decline_findings.py tests/unit/test_author_stem_claimed.py tests/unit/test_closed_sets_remaining.py tests/integration/test_roadmap_ship.py tests/integration/test_roadmap_named_stem.py tests/integration/test_roadmap_refile.py
./dev.py test
```

## Definition of rejected
The Author or requisition-review LLM call runs while `main_writes` is held; any gated section acquires the lock while already holding it (deadlock); the lock is a module global or a per-call object instead of the shared `Checkout` field; drain or serve scheduling changes; or a test fake gains anything besides the `main_writes` attribute.

## Time budget
- expected: 20m
- stuck: 40m
