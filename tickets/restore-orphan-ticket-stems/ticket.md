---
state: confirmed
source: human
priority: P0
kind: chore
---

## Depends on
- none

## Runs before
- clutch-ruff-reclean
- clutch-ruff-reclean-tests-a-l
- clutch-ruff-reclean-tests-m-z
- clutch-verdict-multi-stem
- engine-text-names-clutch-verbs

## Context
- tickets/restore-orphan-ticket-stems/evidence/orphan-evidence.txt
- clutch/status.py::lint_admission
- clutch/status.py::last_states
- clutch/status.py::SETTLED

## Goal / Why
A ticket's stem is its identity in the journal, and the journal is append-only, so a stem can never be renamed: the rename lands on the files and cannot land on the history. Commit `b6512ac5` ("rename chupa to ClutchWork in tickets/ history") renamed ten ticket directories anyway, substituting `clutch` for `chupa` in every path under `tickets/`. The journal still records the ten original stems, with 20 to 78 events each, so `lint_admission` and the scheduler see ten directories no journal event mentions: ten brand-new tickets for work that already ran.

`evidence/orphan-evidence.txt` lists each pair. Nine are a `chupa-` prefix (`chupa-ruff-config` -> `tickets/clutch-ruff-config`, and so on); the tenth is an interior substitution, `engine-text-names-chupa-verbs` -> `tickets/engine-text-names-clutch-verbs`, so matching on the prefix alone misses it. Of the ten, five are blocked on `## Context` paths that moved after they ran (`eval/*` to `tests/harness/`, `tests/test_*.py` to `tests/integration/`, `docs/host-contract.md` to `clutch/docs/`), and five are offered as `ready`, including `clutch-verdict-multi-stem`, whose twin `chupa-verdict-multi-stem` is merged. A drain can start any of those five and redo merged work.

Done means every ticket directory under `tickets/` is named for the stem its journal history is under, so the journal and the files agree on ten identities again and the backlog holds only genuinely unsettled tickets.

This undoes part of `b6512ac5` on purpose. That commit's goal was to retire the old product name, and it is met everywhere a person reads the name: the package, the CLI, the state directory, the README, and the docs. A settled ticket's stem is not a name a person reads; it is the key the journal already wrote. Restoring these ten does not reintroduce the old name as a brand.

## Scope in / Scope out
In:
- Rename each of the ten directories to the stem the journal records, with `git mv`, so git records a pure rename and the run records inside each (`run.md`, `review.md`, `checks.json`, `diagnosis.json`, `attempts/`) move intact:
  - `tickets/clutch-ruff-config` -> `tickets/chupa-ruff-config`
  - `tickets/clutch-ruff-reclean` -> `tickets/chupa-ruff-reclean`
  - `tickets/clutch-ruff-reclean-tests-a-l` -> `tickets/chupa-ruff-reclean-tests-a-l`
  - `tickets/clutch-ruff-reclean-tests-m-z` -> `tickets/chupa-ruff-reclean-tests-m-z`
  - `tickets/clutch-ruff-src` -> `tickets/chupa-ruff-src`
  - `tickets/clutch-ruff-tests-a-k` -> `tickets/chupa-ruff-tests-a-k`
  - `tickets/clutch-ruff-tests-l-z` -> `tickets/chupa-ruff-tests-l-z`
  - `tickets/clutch-test-gates` -> `tickets/chupa-test-gates`
  - `tickets/clutch-verdict-multi-stem` -> `tickets/chupa-verdict-multi-stem`
  - `tickets/engine-text-names-clutch-verbs` -> `tickets/engine-text-names-chupa-verbs`
- Nothing else. No file content changes anywhere, including the `## Context` paths inside the five that name moved files and the `clutch`-for-`chupa` substitutions `b6512ac5` made inside the ticket text. Once each directory matches its journaled stem, `lint_admission` returns `noop` for it and no reader validates its sections again. Repointing a settled ticket's Context would be editing a finished run record.

Out:
- Every other ticket directory. Only these ten have a journaled stem their directory name does not match; the evidence file enumerates the full set from the journal, so no other directory qualifies.
- The journal: nothing is appended, compacted, or rewritten. The ten stems are already settled there; this change makes the files agree with that, not the reverse.
- `clutch/`, `tests/`, and `docs/`: no code or documentation change. The missing check that let the rename pass unnoticed is `lint-flags-orphan-ticket-stem`, which runs ahead of this ticket.
- Renaming the stems inside the ticket text, the journal's own history, or `.clutch/state/chupa.lock`, a dead lockfile from the old state directory.

## Scope fence
- tickets/chupa-ruff-config
- tickets/chupa-ruff-reclean
- tickets/chupa-ruff-reclean-tests-a-l
- tickets/chupa-ruff-reclean-tests-m-z
- tickets/chupa-ruff-src
- tickets/chupa-ruff-tests-a-k
- tickets/chupa-ruff-tests-l-z
- tickets/chupa-test-gates
- tickets/chupa-verdict-multi-stem
- tickets/clutch-ruff-config
- tickets/clutch-ruff-reclean
- tickets/clutch-ruff-reclean-tests-a-l
- tickets/clutch-ruff-reclean-tests-m-z
- tickets/clutch-ruff-src
- tickets/clutch-ruff-tests-a-k
- tickets/clutch-ruff-tests-l-z
- tickets/clutch-test-gates
- tickets/clutch-verdict-multi-stem
- tickets/engine-text-names-chupa-verbs
- tickets/engine-text-names-clutch-verbs

## Acceptance criteria
1. `uv run clutch lint chupa-ruff-config chupa-ruff-reclean chupa-ruff-reclean-tests-a-l chupa-ruff-reclean-tests-m-z chupa-ruff-src chupa-ruff-tests-a-k chupa-ruff-tests-l-z chupa-test-gates chupa-verdict-multi-stem engine-text-names-chupa-verbs` prints `lint: 0/0 tickets valid` and exits 0: each stem's ticket file exists and the journal records it settled or rejected, so `lint_admission` returns `noop` and none is counted or validated. Exit 2 (`no ticket file`) or any non-zero count means a directory is still misnamed.
2. `uv run clutch lint` exits 0 or 1 and its output names no `clutch-ruff-`, `clutch-test-gates`, or `engine-text-names-clutch-verbs` ticket, where before this change it reported 15 `## Context` findings across five of them. A finding against a ticket outside this fence does not fail this criterion.
3. `git diff --find-renames --name-status <merge base>..HEAD -- tickets/` reports only `R100` rename entries, every one of them between a pair listed in `## Scope in`, and no `A`, `D`, or `M` entry under `tickets/` other than this ticket's own directory. No byte inside any moved file changed.
4. `ls tickets | grep -E '^(clutch-ruff-|clutch-test-gates$|engine-text-names-clutch-verbs$)'` finds nothing, and `tickets/chupa-ruff-config/run.md`, `tickets/chupa-test-gates/review.md`, `tickets/chupa-ruff-config/attempts/0/harvest.json`, and `tickets/engine-text-names-chupa-verbs/run.md` all exist and are readable.
5. `./dev.py test` exits 0.

## Verification
```
./dev.py test
```

## Definition of rejected
- Any file content under `tickets/` changes; the change is not a pure set of renames.
- A `## Context`, `## Scope fence`, or any other section inside one of the ten settled tickets is repointed or rewritten.
- The journal is appended to, compacted, deleted, or rewritten, or a verdict verb is run against any of the ten to clear it from the backlog.
- A ticket directory is deleted rather than renamed.
- Fewer than ten directories are renamed, or a directory outside the twenty fenced paths is touched.
- Code, tests, or documentation under `clutch/`, `tests/`, or `docs/` changes.

## Time budget
- expected: 15m
- stuck: 45m
