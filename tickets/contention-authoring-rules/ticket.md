---
state: confirmed
source: human
priority: P1
kind: chore
---

## Depends on
- none

## Runs before
- release-verb
- fence-closure-registries
- unit-criteria-disk-snag

## Context
- docs/parallel-tickets-plan.md#7. Contention rules: small tests, small tickets
- docs/parallel-tickets-plan.md#Where each rule lives
- clutch/docs/host-authoring.md
- CLAUDE.md#A. Engine conduct
- AGENTS.md
- clutch/hostfiles.py::parse
- tests/unit/test_host_authoring.py

## Goal / Why
The contention rules of `docs/parallel-tickets-plan.md` section 7 are in no rule file. `clutch/docs/host-authoring.md` says nothing about where a ticket's new tests or fixtures go or how far a fence should reach, and `CLAUDE.md` and `AGENTS.md` name no test file to keep new tests out of. So tickets keep adding tests and helpers to the closest large file. Measured at `c761b213` over the 554 `tickets/*/ticket.md` fences (counting each file's pre-move `tests/<name>` path too): `tests/integration/test_stages.py` is fenced 55 times, `test_drain.py` 42, `test_watch.py` 38, `test_daemon_composition.py` 31, `test_cli.py` 29, `test_mergequeue.py` 20. Those modules double as fixture libraries: `test_cli.py` is imported by 60 test modules, `test_drain.py` by 37, `test_stages.py` by 33, `test_daemon_composition.py` by 21, `serve_rig.py` by 16, `test_mergequeue.py` by 13, and no `conftest.py` exists. Two tickets that fence one file collide at merge, and the parallel plan's dispatch will run them one after the other.

After this change the authoring guide, which every authoring surface reads and `clutch/author.py` embeds in the Author prompt, carries the four generic contention rules, and this repo's own rules carry the do-not-grow list with its paved road. Tickets authored from now on, including the rest of 0.2.0, put new tests in new files. Owner decision 4 (`docs/roadmap.md` section 6) puts this rule in 0.2.0 and the splitting of the large files in later chores.

The list is re-measured, not copied from the plan. The plan's five files (`test_daemon_composition.py`, `test_drain.py`, `test_mergequeue.py`, `test_stages.py`, `serve_rig.py`, measured at `80b76d5d`) stay. The re-measurement adds `test_cli.py` (905 lines, the most-imported test module, 29 fences) and `test_watch.py` (38 fences, 44 commits since 2026-11-01), both hotter than `test_mergequeue.py` (1,230 lines, 20 fences, 15 commits since 2026-11-01). `tests/unit/test_specs.py` (60 fences) stays off the list: its edits are forced version pins from spec bumps, so keeping new tests out of it frees no fence.

## Scope in / Scope out
Rule homes (CLAUDE.md "A rule has one of two homes" and "One authoring process"):
- The four generic rules go in `clutch/docs/host-authoring.md`, the one source of ticket content rules, which reaches every host. They do not go in `CORE_TEMPLATE`: they are authoring rules, not conduct rules, and the template is at 7,855 of 8,192 bytes.
- The do-not-grow list names this repo's files, so it goes in `CLAUDE.md` and `AGENTS.md` outside the managed block. It goes in `CLAUDE.md` section A, not section B as the plan's "Where each rule lives" table says: section B opens by saying it governs the human-present chat session, and this rule must bind Author and Implement too.

Scope in:
1. `clutch/docs/host-authoring.md`: add this section between the end of the `## What each section is for` list (after the `Time budget` bullet) and `## Path matching`, with this text:

   ```
   ## Keeping tickets apart

   A file that many tickets fence makes their changes collide. Keep new work out of shared files:

   - Put a ticket's new tests in a new test file named for the behavior it covers. Fence an
     existing test file only when the change forces an edit there (see `Scope fence`) or the file
     covers the edited unit and nothing else. Never add tests to a file just because it is the
     closest match.
   - Put a new fixture, helper, rig, or data set in a new module next to its tests. Change a shared
     fixture, `conftest.py`, harness, or rig only when that fixture is the ticket's subject: do that
     in its own ticket, and the tickets that use it list it in `Depends on`.
   - A ticket fences only the files its change forces. A fence that spans more than one subsystem
     is usually two tickets: link them with `Depends on` when the second needs the first's merged
     code, otherwise with `Runs before`.
   - A documentation update edits only the section the change makes false.
   ```

2. `CLAUDE.md` section A, directly after the `**Verification uses `./dev.py test`.**` rule and its `Why:` line, and `AGENTS.md`'s `## Engine conduct` section outside the managed block, directly after its `**Verification uses `./dev.py test`.**` rule and `Why:` line: add this rule, identical in both files:

   ```
   - **Keep new tests out of the hot test files.** No new test, fixture, or helper goes into `tests/integration/test_daemon_composition.py`, `tests/integration/test_drain.py`, `tests/integration/test_mergequeue.py`, `tests/integration/test_stages.py`, `tests/integration/test_cli.py`, `tests/integration/test_watch.py`, or `tests/integration/serve_rig.py`. A new test goes in a new `tests/unit/test_<module>_<behavior>.py` or `tests/integration/test_<behavior>.py`, and a new fixture or helper in a new module next to it. Fence one of these files only when the change forces an edit there.
     Why: at `c761b213` they are this repo's most-fenced and most-imported test files (`test_stages.py` is in 55 ticket fences; `test_cli.py` is imported by 60 test modules), so a ticket that grows one collides with most others. (`docs/parallel-tickets-plan.md` section 7)
   ```

3. New `tests/integration/test_contention_rules.py`, following the rule it adds. It goes under `tests/integration/` because it reads repo files, which `docs/how-clutch-works.md` section 2.2 keeps out of the unit suite. It defines a module constant `DO_NOT_GROW` holding the seven paths of item 2 and the two tests of the acceptance criteria. It reads `clutch/docs/host-authoring.md`, `CLAUDE.md`, and `AGENTS.md` from the repo root (`Path(__file__).resolve().parents[2]`) and splits the conduct files with `clutch.hostfiles.parse`.

The change only adds text. Every existing sentence of the three documents stays as it is, including the phrases `tests/unit/test_host_authoring.py` pins.

Scope out:
- `CORE_TEMPLATE` in `clutch/hostfiles.py` and the managed blocks of `CLAUDE.md` and `AGENTS.md`. Do not run `clutch core`.
- `docs/parallel-tickets-plan.md` and `docs/roadmap.md`. A person links the authored row and updates plan status (`docs/roadmap.md` section 9).
- `docs/how-clutch-works.md`: section 2.2 describes the two suites and stays true.
- The seven listed files themselves: no move, no split, no edit. Owner decision 4 schedules the splits as separate chores.
- `tests/unit/test_host_authoring.py`: no new test goes there.
- `tests/conftest.py`, shared fakes, and fixture migration (`test-fakes-and-conftest`).
- Prompt specs under `clutch/specs/`: Author embeds the guide at run time, so no spec text changes and no version bumps.
- Any lint, gate, or check that enforces these rules. They are behavioral rules, and the prose is their enforcement.

## Scope fence
- clutch/docs/host-authoring.md
- CLAUDE.md
- AGENTS.md
- tests/integration/test_contention_rules.py

## Acceptance criteria
1. `tests/integration/test_contention_rules.py::test_authoring_guide_states_contention_rules` reads `clutch/docs/host-authoring.md` and asserts it contains each of `new test file named for the behavior it covers`, `in a new module next to its tests`, `fences only the files its change forces`, and `edits only the section the change makes false`, and that it contains none of the seven `DO_NOT_GROW` paths. Ruled out: a guide missing any one of the four rules (today's guide fails all four), and the repo's own list written into the guide that every host installs.
2. `tests/integration/test_contention_rules.py::test_do_not_grow_list_is_a_repo_rule` does three things. For each of `CLAUDE.md` and `AGENTS.md`, it takes the project text after the managed block (`hostfiles.parse(data)[1]`) and asserts that the text contains every `DO_NOT_GROW` path wrapped in backticks, plus `` `tests/unit/test_<module>_<behavior>.py` `` and `` `tests/integration/test_<behavior>.py` ``. It asserts that each `DO_NOT_GROW` path is an existing file under the repo root. It asserts that no `DO_NOT_GROW` path occurs in `hostfiles.CORE_TEMPLATE`. Ruled out: the rule in `CLAUDE.md` only (lost parity), the rule written into a managed block or `CORE_TEMPLATE` instead of the project text, a prohibition with no paved road, and a mistyped or stale path.
3. `./dev.py test tests/unit/test_host_authoring.py tests/integration/test_author.py tests/integration/test_hostfiles.py` exits 0. The guide keeps every phrase it already pins, Author still embeds the guide byte for byte, and both conduct files' core markers still parse. Ruled out: an edit that rewords a pinned sentence or breaks a `clutch:core` marker.
4. `./dev.py test` exits 0.

## Verification
```
./dev.py test tests/integration/test_contention_rules.py
./dev.py test tests/unit/test_host_authoring.py tests/integration/test_author.py tests/integration/test_hostfiles.py
./dev.py test
```

## Definition of rejected
The branch is rejected if it:
- changes `CORE_TEMPLATE`, a managed block, or any file outside the fence;
- writes the do-not-grow list or any repo path into `clutch/docs/host-authoring.md`;
- restates the four generic rules in `CLAUDE.md` or `AGENTS.md` instead of keeping them in the guide;
- gives the two conduct files different rule text;
- rewords or removes an existing sentence of the three documents;
- adds a lint, gate, config knob, or spec change to enforce the rules;
- moves or splits a test file.

## Time budget
- expected: 25m
- stuck: 75m
