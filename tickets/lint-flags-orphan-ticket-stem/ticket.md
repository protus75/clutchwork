---
state: confirmed
source: human
priority: P0
kind: feature
---

## Depends on
- none

## Runs before
- restore-orphan-ticket-stems

## Context
- clutch/tickets.py::lint_findings
- clutch/tickets.py::intake
- clutch/tickets.py::_intake_plan_stem
- clutch/tickets.py::ticket_path
- clutch/status.py::lint_admission
- clutch/status.py::last_states
- clutch/__main__.py::_lint
- clutch/docs/host-authoring.md#Workflow
- tests/unit/test_ticket_lint_rules.py
- tests/unit/test_lint_ceiling.py

## On-demand
- tests/integration/test_lint_verb.py

## Goal / Why
A ticket's stem is its key in the journal. The journal is append-only, so renaming a settled ticket's directory cannot move its history: the stem keeps 20 to 78 events under the old name while the directory answers to a new one. Nothing notices. `lint_admission` skips a stem the journal records as settled, so the old name is never validated and never listed; the new name has no events at all, so it is admitted as a brand-new ticket and the scheduler offers already-merged work as `ready`.

That happened in this repo on 2026-11-15: commit `b6512ac5` substituted `clutch` for `chupa` in every path under `tickets/` and orphaned ten stems in one commit, five of them offered as `ready`, one of them (`chupa-verdict-multi-stem`) already merged. `tickets/restore-orphan-ticket-stems/evidence/orphan-evidence.txt` records it. The rename was a single sweep and nothing refused it; a rule in an agent's head is what let it through, so the rule needs a check.

The signal is already on disk and is decisive: the engine writes `run.md`, `review.md`, `checks.json`, `diagnosis.json`, and `attempts/` into a ticket directory only during a run, and `intake` journals `ticket_intake` for a stem before any of them is written. So a directory holding any engine-written artifact while its stem has zero journal events is always an orphaned identity, and never a ticket a person just authored (`ticket.md` and `evidence/` only) or one mid-run (artifacts and events both).

Done means `clutch lint` reports an orphaned ticket identity as a finding with a paved road, and `intake` refuses to admit one, so a rename that orphans a stem is caught the next time either runs instead of surfacing as phantom work weeks later.

## Scope in / Scope out
In:
- Add one pure helper to `clutch/tickets.py`, beside `lint_findings`: given a stem, the journal events, and the repo, it returns a `Finding` when every one of these holds, and `None` otherwise.
  - The journal records at least one event carrying a ticket. A repo whose `.clutch/state` was never cloned has no journal, every stem has zero events, and the check must stay silent there rather than flag every ticket at once.
  - The stem has zero events of its own.
  - `tickets/<stem>/` holds at least one of `run.md`, `review.md`, `checks.json`, `diagnosis.json`, or an `attempts/` directory.
- The finding's message names the stem and the artifacts found. Its paved road names both roads: rename `tickets/<stem>/` to the stem the journal records those artifacts under, or, if the work is genuinely new, remove the copied artifacts so only `ticket.md` and `evidence/` remain.
- `_lint` in `clutch/__main__.py` already reads the journal into `events` and resolves a linked worktree's journal to the main checkout's; it calls the helper for each admitted stem and prints the finding with the existing finding format, so the stem counts as invalid.
- `intake` in `clutch/tickets.py` already folds `last_states(journal.read())`; it calls the same helper and routes the finding into the stem's refusal, so a drain or serve refuses to admit an orphaned identity instead of queueing it.
- `clutch/docs/host-authoring.md`, the `Workflow` section: one sentence that lint and intake refuse a ticket directory holding run artifacts that the journal does not know the stem by, and what to do about it. Lint's behavior is documented there, so the document lands with the check.

Out:
- Guessing or applying the right stem. The check reports; a person or `restore-orphan-ticket-stems` renames. No automatic rename, no alias table, no stem-history record in the journal.
- Matching on the old product name. The rule is journal identity, not a substring: one of the ten orphans is `engine-text-names-chupa-verbs`, where the substitution is interior, and a prefix or `chupa` match would both miss it and expire the moment the next rename uses different words.
- `clutch/status.py`: `lint_admission` keeps deciding refuse, noop, and admit as it does. An orphan has no events, so it is already admitted and reaches the findings; no admission change is needed.
- The 526 settled tickets whose directories match their stems, and the ten already-orphaned directories. Fixing those is `restore-orphan-ticket-stems`, which this ticket runs ahead of so the check exists before the repair.
- `clutch doctor`, the snapshot, and the extension: no new surface. The finding reaches the extension already, as the `invalid:` status every lint finding produces.

## Scope fence
- clutch/tickets.py
- clutch/__main__.py
- clutch/docs/host-authoring.md
- tests/unit/test_orphan_ticket_stem.py
- tests/integration/test_lint_verb.py

## Acceptance criteria
1. `tests/unit/test_orphan_ticket_stem.py` asserts the helper returns a `Finding` for a stem with zero events whose directory holds `run.md`, given a journal that has events for some other ticket, and that the finding's paved road names both renaming the directory and removing the artifacts.
2. `tests/unit/test_orphan_ticket_stem.py` asserts `None` for each of: a stem with zero events whose directory holds only `ticket.md` (just authored); a stem whose directory holds `run.md` and that has at least one event of its own (mid-run or merged); and a stem with zero events holding `run.md` when the journal carries no ticket-bearing event at all (no journal cloned). The third case must return `None`, not a finding.
3. `tests/unit/test_orphan_ticket_stem.py` asserts the helper fires on each of `review.md`, `checks.json`, `diagnosis.json`, and an `attempts/` directory on its own, not only `run.md`.
4. `tests/integration/test_lint_verb.py` asserts `clutch lint` over a fixture repo containing an orphaned directory exits 1 and prints the finding naming that stem, and that the same repo lints clean once the directory is renamed to the journaled stem: `lint: 0/0 tickets valid`, exit 0, because the journaled stem is settled and `lint_admission` noops it.
5. `tests/integration/test_lint_verb.py` asserts `intake` refuses the orphaned stem, returning it in the result's `refused` mapping with the orphan finding, and does not journal a `ticket_intake` signal for it.
6. `grep -n chupa clutch/tickets.py clutch/__main__.py` finds nothing: the rule is journal identity, not a name match.
7. `clutch/docs/host-authoring.md` gains the sentence, and `grep -c "run artifacts" clutch/docs/host-authoring.md` is at least 1.
8. `./dev.py test` exits 0.

## Verification
```
./dev.py test
```

## Definition of rejected
- The check matches on `chupa`, on a name prefix, or on any product name instead of on journal identity.
- The check renames a directory, writes an alias or stem-history record, or appends to the journal.
- The check fires when the journal carries no ticket-bearing event, so a clone without `.clutch/state` reports every ticket as orphaned.
- The check fires on a ticket mid-run, which has both artifacts and events, or on a freshly authored ticket holding only `ticket.md` and `evidence/`.
- `lint` reports the finding but `intake` still admits the stem, or the reverse.
- Any of the ten already-orphaned directories is renamed in this ticket.

## Time budget
- expected: 40m
- stuck: 90m
