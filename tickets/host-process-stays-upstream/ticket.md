---
state: confirmed
source: human
priority: P1
kind: feature
---

## Depends on
- none

## Context
- clutch/author.py::author
- clutch/author.py::failure_declined
- clutch/hostfiles.py::CORE_TEMPLATE
- tests/integration/test_author.py::test_reopened_retro_ticket_starts_draft
- tests/integration/test_hostfiles.py::test_core_template_is_host_neutral
- docs/how-clutch-works.md#9.3 Author and starting state

## Goal / Why
A host's pipeline can turn a repair that belongs in clutch into a host ticket that copies or patches clutch's rule in host files. On 2026-11-11 the fungo host's retro 22 (`tickets/retro/000022.md` in fungo) proposed `"proposed_spec_paths": ["specs/implement.md"]`, a repair to clutch's implement spec. `author()` in `clutch/author.py` passes these to the Author model as `clutch/specs/implement.md`. Fungo does not track that file, because the clutch install owns it. The model wrote `testing-assertions-filter-tiebreak-clause` instead: a fungo ticket that pastes a restated implement rule into fungo's `docs/TESTING.md`. The owner rejected it. A host copy of a clutch rule competes with clutch's version, reaches no other host, and goes stale on upgrade. Repositories do not cross-talk, so the fix is not to file into clutch from a host. It is to stop the host from authoring a substitute, and to leave a record the owner can carry upstream by hand.

When this ticket is done:
- A `retro_finding` with any proposed spec path that the repository does not track is declined before any Author model call. Its decision record in `tickets/decisions/` names each untracked path and the retro report key, so the owner can carry the proposal to clutch. No host ticket is authored. In this repo, clutch tracks its own specs, so its retro spec proposals are authored as before.
- Every host's managed conduct block carries a rule that tells sessions and ticket agents not to copy or patch clutch process into host files.

Rule home: the new rule applies to every host, so its home is `CORE_TEMPLATE` in `clutch/hostfiles.py`. It reaches this repo's `CLAUDE.md` and `AGENTS.md` through `./dev.py core`. Nothing is added outside the managed blocks.

## Scope in / Scope out
Scope in:
- `clutch/author.py`, `author()`: move the tracked-files listing (`checkout.git.ls_files`) above the Author spec load. Directly after it, decline when the message's `proposed_spec_paths` contains any path whose repo form `clutch/<path>` is not a tracked file. The guard runs before `author()` reads the Author spec, any report, or calls the model, so a unit test reaches it with a fake checkout. Decline through the existing `failure_declined`. Its evidence string names every untracked `clutch/<path>`, includes the message's `retro_report_key`, and states that the clutch install owns these specs, so the owner carries the proposal to clutch. A message with no proposed spec paths, or one whose proposed spec paths are all tracked, proceeds unchanged.
- `tests/unit/test_author.py`: add a parametrized test that calls `author()` on a `retro_finding` message with an `author` verdict. It uses a fake checkout whose `git.ls_files` returns a fixed list, and monkeypatches `failure_declined` to record its evidence and return a sentinel. Case 1: `proposed_spec_paths=["specs/implement.md"]`, with a tracked list that has no `clutch/specs/` file. Case 2: `["specs/review.md", "specs/implement.md"]`, with `clutch/specs/review.md` tracked. For both cases, assert that `author()` returns the sentinel, and that the evidence contains `clutch/specs/implement.md` and the message's retro report key. Case 2 also asserts that the evidence does not contain `clutch/specs/review.md`.
- `tests/unit/test_hostfiles.py` is fenced because `clutch/hostfiles.py` has a unit coverage floor. Edit it only if the template change breaks it.
- `tests/integration/test_author.py`: the existing tests `test_author_uses_baseline_resolution` (its `retro_finding` row), `test_reopened_retro_ticket_starts_draft`, `test_retro_author_bridge_and_resolution_recover_without_another_call`, and `test_merged_fix_recurrence_can_author_new_ticket` must commit a fixture file at `clutch/<path>` for each of their proposed spec paths before their first `_run`, so they keep exercising the authored path. Their assertions are unchanged.
- `clutch/hostfiles.py`, `CORE_TEMPLATE`: append this bullet, verbatim, as the last bullet of `## Diagnosis`:
  `- HARD: A fix that belongs in clutch (a prompt spec, gate, ticket format, host guide, or this block) is never copied or patched into host files. Report it for the owner to carry to clutch, then stop. Why: a host copy competes with clutch's rule, reaches no other host, and goes stale on upgrade.`
- Run `./dev.py core` to refresh the managed blocks in `CLAUDE.md` and `AGENTS.md`. `core` does not route `hosts/fixture/CLAUDE.md`, so rewrite that file to `hostfiles.render` of its current bytes.
- `tests/integration/test_hostfiles.py`: regenerate `GOLDEN` with the module's `__main__` block. In `test_core_template_is_host_neutral`, add one pinned phrase: `is never copied or patched into host files`.
- `docs/how-clutch-works.md`, section `9.3 Author and starting state`: add one sentence. It says that a `retro_finding` naming a spec path the repository does not track is declined before the Author call, with a decision record that names the paths and the retro report for the owner to carry to clutch.

Scope out:
- `clutch/specs/retro.md`, `clutch/specs/triage.md`, `clutch/specs/author.md`, and every other prompt spec. The retro still proposes spec repairs in a host, because the proposal is the evidence the owner carries upstream.
- Any write to a repository other than the one being triaged, and any channel from a host to clutch's Suggestion Box.
- `suggestion` and other message classes, and the `test_issue` / `proposed_paths` proposal form.
- Text outside the `clutch:core` markers in `CLAUDE.md`, `AGENTS.md`, and `hosts/fixture/CLAUDE.md`. Every other `CORE_TEMPLATE` bullet.

## Scope fence
- clutch/author.py
- clutch/hostfiles.py
- CLAUDE.md
- AGENTS.md
- hosts/fixture/CLAUDE.md
- docs/how-clutch-works.md
- tests/integration/test_author.py
- tests/integration/test_hostfiles.py
- tests/unit/test_author.py
- tests/unit/test_hostfiles.py

## Acceptance criteria
1. `./dev.py test tests/unit/test_author.py` passes, including the new parametrized decline test. If the guard is missing, `author()` goes on to the spec load instead of returning the sentinel, which fails case 1. If the guard declines only when no proposed path is tracked, case 2 never declines and fails. If the evidence omits the untracked path or the retro report key, both cases fail.
2. `./dev.py test tests/integration/test_author.py` passes. `test_author_uses_baseline_resolution`, `test_reopened_retro_ticket_starts_draft`, `test_retro_author_bridge_and_resolution_recover_without_another_call`, and `test_merged_fix_recurrence_can_author_new_ticket` still author their tickets, with their fixture spec files tracked. A guard that declines every spec proposal fails them.
3. `./dev.py test tests/integration/test_hostfiles.py` passes. `test_core_template_is_host_neutral` fails if `CORE_TEMPLATE` lacks `is never copied or patched into host files`, and the size test fails if the template exceeds 8192 bytes.
4. `./dev.py test tests/integration/test_fixture_host.py` passes, and the `core_drift` gate passes. `classify_core` reports `current` for `CLAUDE.md`, `AGENTS.md`, and `hosts/fixture/CLAUDE.md`, so a hand-edited or stale managed block fails.
5. `docs/how-clutch-works.md` section `9.3 Author and starting state` states the untracked-spec decline.
6. `./dev.py test` exits 0.

## Verification
```
./dev.py test tests/unit/test_author.py tests/unit/test_hostfiles.py tests/integration/test_author.py tests/integration/test_hostfiles.py tests/integration/test_fixture_host.py
./dev.py test
```

## Definition of rejected
- A retro spec proposal whose paths are all tracked is declined, or any message class other than `retro_finding` is affected.
- The change writes to, or files into, any repository other than the one being triaged.
- Any prompt spec changes, or the retro stops proposing spec paths in a host.
- The new `CORE_TEMPLATE` bullet differs from the Scope in text or sits outside `## Diagnosis`, or another template bullet changes.
- `CLAUDE.md`, `AGENTS.md`, or `hosts/fixture/CLAUDE.md` changes outside its `clutch:core` markers.

## Time budget
- expected: 35m
- stuck: 80m
