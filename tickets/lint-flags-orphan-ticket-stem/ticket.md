---
state: confirmed
source: human
priority: P0
kind: feature
---

## Depends on
- none

## Context
- clutch/tickets.py::lint_findings
- clutch/tickets.py::ticket_path
- clutch/status.py::lint_admission
- clutch/status.py::last_states
- clutch/__main__.py::_lint
- clutch/drain.py::_Drain._scan
- clutch/drain.py::_Scan
- clutch/drain.py::Parked
- clutch/docs/host-authoring.md#Workflow
- tests/unit/test_ticket_lint_rules.py
- tests/unit/test_drain_deadline.py
- tests/unit/test_drain_report_intake.py

## On-demand
- tests/integration/test_lint_verb.py

## Goal / Why
A ticket's stem is its key in the journal. The journal is append-only, so renaming a settled ticket's directory cannot move its history: the stem keeps 20 to 78 events under the old name while the directory answers to a new one. Nothing notices. `lint_admission` and `_scan` both skip a stem the journal records as settled, so the old name is never validated and never listed; the new name has no events at all, so it passes every check and the drain offers already-merged work as `ready`.

That happened in this repo on 2026-11-15: commit `b6512ac5` substituted `clutch` for `chupa` in every path under `tickets/` and orphaned ten stems in one commit, five of them offered as `ready`, one of them (`chupa-verdict-multi-stem`) already merged. `tickets/restore-orphan-ticket-stems/evidence/orphan-evidence.txt` records it. The rename was a single sweep and nothing refused it; a rule in an agent's head is what let it through, so the rule needs a check.

The signal is already on disk and is decisive: the engine writes `run.md`, `review.md`, `checks.json`, `diagnosis.json`, and `attempts/` into a ticket directory only during a run, and `intake` journals `ticket_intake` for a stem before any of them is written. So a directory holding any engine-written artifact while its stem has zero journal events is always an orphaned identity, and never a ticket a person just authored (`ticket.md` and `evidence/` only) or one mid-run (artifacts and events both).

Done means both readers of a committed ticket directory refuse an orphaned identity: `clutch lint` reports it as a finding with a paved road, and the drain's `_scan` treats it as invalid so it is parked with that finding instead of dispatched. A rename that orphans a stem then surfaces the next time either runs, not as phantom work weeks later.

## Scope in / Scope out
In:
- Add one pure helper to `clutch/tickets.py`, beside `lint_findings`: given a stem, the journal events, and the repo, it returns a `Finding` when every one of these holds, and `None` otherwise.
  - The journal records at least one event carrying a ticket. A repo whose `.clutch/state` was never cloned has no journal, every stem has zero events, and the check must stay silent there rather than flag every ticket at once.
  - The stem has zero events of its own.
  - `tickets/<stem>/` holds at least one of `run.md`, `review.md`, `checks.json`, `diagnosis.json`, or an `attempts/` directory.
- The finding's message names the stem and the artifacts found. Its paved road names both roads: rename `tickets/<stem>/` to the stem the journal records those artifacts under, or, if the work is genuinely new, remove the copied artifacts so only `ticket.md` and `evidence/` remain.
- `_lint` in `clutch/__main__.py` already reads the journal into `events` and resolves a linked worktree's journal to the main checkout's; it calls the helper for each admitted stem and prints the finding in the existing finding format, so the stem counts as invalid and `lint` exits 1.
- `_scan` in `clutch/drain.py` already skips settled stems and collects a findings string per stem in its `invalid` mapping. After that skip and before `parse_ticket`, it calls the same helper with the events it already folded for `states`, and on a finding writes the stem into `invalid` and continues, so the stem never enters `tickets` and the existing parked path reports it. No new parking machinery, no new `Parked` field, no new state.
- `clutch/docs/host-authoring.md`, the `Workflow` section: one sentence that lint and the drain refuse a ticket directory holding run artifacts that the journal does not know the stem by, and what to do about it. Lint's behavior is documented there, so the document lands with the check.

Out:
- `intake` in `clutch/tickets.py`. It processes only stems pending in porcelain, so a committed rename, which is this incident's shape, never reaches it. The two surfaces in scope cover both shapes: `_scan` reads committed directories, and `lint` reads pending ones too.
- Guessing or applying the right stem. The check reports; a person or `restore-orphan-ticket-stems` renames. No automatic rename, no alias table, no stem-history record in the journal.
- Matching on the old product name. The rule is journal identity, not a substring: one of the ten orphans is `engine-text-names-chupa-verbs`, where the substitution is interior, and a prefix or `chupa` match would both miss it and expire the moment the next rename uses different words.
- `clutch/status.py`: `lint_admission` keeps deciding refuse, noop, and admit as it does. An orphan has no events, so it is already admitted and reaches the findings.
- The settled tickets whose directories match their stems. The ten directories that commit `b6512ac5` orphaned were renamed back to their journaled stems in commit `001d3baf`, so no orphan remains for this check to find in this repo; it exists to refuse the next one.
- `clutch doctor`, the snapshot, and the extension. The finding surfaces in `clutch lint` and in the drain's parked report, and nowhere else: `load_tickets` in `clutch/observe.py` builds a row's `invalid:` status from `parse_ticket` errors only, so neither a `lint_findings` finding nor this one reaches the snapshot, and `clutch status` keeps listing an orphan among its queued rows until the drain parks it. Carrying lint findings into the snapshot is a separate change for a separate ticket.

## Scope fence
- clutch/tickets.py
- clutch/__main__.py
- clutch/drain.py
- clutch/docs/host-authoring.md
- tests/unit/test_orphan_ticket_stem.py
- tests/integration/test_lint_verb.py

## Acceptance criteria
1. `tests/unit/test_orphan_ticket_stem.py` asserts the helper returns a `Finding` for a stem with zero events whose directory holds `run.md`, given a journal that has events for some other ticket, and that the finding's paved road names both renaming the directory and removing the artifacts.
2. `tests/unit/test_orphan_ticket_stem.py` asserts `None` for each of: a stem with zero events whose directory holds only `ticket.md` (just authored); a stem whose directory holds `run.md` and that has at least one event of its own (mid-run or merged); and a stem with zero events holding `run.md` when the journal carries no ticket-bearing event at all (no journal cloned). The third case must return `None`, not a finding.
3. `tests/unit/test_orphan_ticket_stem.py` asserts the helper fires on each of `review.md`, `checks.json`, `diagnosis.json`, and an `attempts/` directory on its own, not only `run.md`.
4. `tests/unit/test_orphan_ticket_stem.py` drives `clutch.__main__._lint` with a fake checkout, following `tests/unit/test_ticket_lint_rules.py::test_lint_verb_prints_carried_file_finding`, over a journal holding another stem's event and a directory reporting `run.md`: it asserts exit 1 and that the printed output names the orphan stem and its paved road. This criterion runs the new lines in `clutch/__main__.py`, which `test-gate.toml` floors at 13.
5. `tests/unit/test_orphan_ticket_stem.py` drives `clutch.drain._Drain._scan` with fake git, journal, and filesystem, following `tests/unit/test_drain_deadline.py`, over the same shape: it asserts the orphan stem is a key of the returned `_Scan`'s `invalid` mapping with a value naming the orphan finding, and is absent from its `tickets` mapping. It also asserts a stem with its own events and a `run.md` lands in `tickets`, not `invalid`. This criterion runs the new lines in `clutch/drain.py`, which `test-gate.toml` floors at 10.
6. `tests/integration/test_lint_verb.py` asserts `clutch lint` over a fixture repo containing an orphaned directory exits 1 and prints the finding naming that stem, and that the same repo lints clean once the directory is renamed to the journaled stem: `lint: 0/0 tickets valid`, exit 0, because the journaled stem is settled and `lint_admission` noops it.
7. `grep -n chupa clutch/tickets.py clutch/__main__.py clutch/drain.py` finds nothing: the rule is journal identity, not a name match.
8. `clutch/docs/host-authoring.md` gains the sentence, and `grep -c "run artifacts" clutch/docs/host-authoring.md` is at least 1.
9. `./dev.py test` exits 0.

## Verification
```
./dev.py test
```

## Definition of rejected
- The check matches on `chupa`, on a name prefix, or on any product name instead of on journal identity.
- The check renames a directory, writes an alias or stem-history record, or appends to the journal.
- The check fires when the journal carries no ticket-bearing event, so a clone without `.clutch/state` reports every ticket as orphaned.
- The check fires on a ticket mid-run, which has both artifacts and events, or on a freshly authored ticket holding only `ticket.md` and `evidence/`.
- `lint` reports the finding but `_scan` still admits the stem, or the reverse.
- `_scan` gains a new parked reason, `Parked` field, or state instead of reusing its `invalid` mapping.
- Any of the ten already-orphaned directories is renamed in this ticket.

## Time budget
- expected: 45m
- stuck: 100m
