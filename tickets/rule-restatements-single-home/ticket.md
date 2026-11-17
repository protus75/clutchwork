---
state: confirmed
source: human
priority: P1
kind: chore
---

## Depends on
- none

## Context
- docs/how-clutch-works.md#3.2 Intake
- docs/how-clutch-works.md#4.2 Implement
- docs/how-clutch-works.md#5.2 Bug tickets
- clutch/docs/host-contract.md#Managed conduct and ticket ownership
- clutch/docs/host-authoring.md#Unit and integration tests
- clutch/docs/host-authoring.md#Bug tickets
- clutch/hostfiles.py::CORE_TEMPLATE
- tests/integration/test_unit_io_rule.py

## Goal / Why
Roadmap row 126 (`docs/roadmap.md` section 8, release 0.4.0). Section 2.5 of the roadmap audit, "Rules stated in more than one home", recurred in 0.3.0: maintained documents restate rules whose home is elsewhere, and its rule is "Specs may restate a rule the model needs; documents may not." A rule changed in its home leaves the copies saying otherwise. That already happened once: `unit-test-io-rule-one-home` (box-000477, box-000484) found the unit-test I/O rule stated differently in the specs and in `docs/how-clutch-works.md`, and had to edit both document copies to agree.

The row cites the restatements by line number from the audit. Found by content at HEAD `89c93b40`, four remain:

1. `clutch/docs/host-contract.md`, section `## Managed conduct and ticket ownership`: "Do not hand-edit the core: `clutch core` inserts or refreshes it, then commit the routed files." It restates the managed block's own `Engine conduct` bullet, "Never hand-edit this managed block; change the engine template and run clutch core to refresh it.", whose home is `CORE_TEMPLATE` in `clutch/hostfiles.py`.
2. `docs/how-clutch-works.md` section 3.2 Intake, the bullet that begins "Every ticket read (intake, lint, confirm, drain, serve, run, and Author) refuses a bug without regular, non-symlink evidence" and ends "when the journal records settlement."
3. `docs/how-clutch-works.md` section 5.2 Bug tickets, the three sentences from "Every ticket read (intake, lint, confirm, drain, serve, run, and Author) refuses a bug without regular, non-symlink evidence." to "Settled and rejected tickets are exempt, including at intake when the journal records settlement." Items 2 and 3 restate the bug-evidence rule of `clutch/docs/host-authoring.md` `### Evidence`.
4. `docs/how-clutch-works.md` section 4.2 Implement, the paragraph that begins "The Implement prompt separates unit and integration suites." It restates the unit-test I/O rule of `clutch/docs/host-authoring.md` `## Unit and integration tests` and the test rules of `clutch/specs/implement.md`.

The home of each rule, under `CLAUDE.md` "A rule has one of two homes" and "One authoring process":
- Never hand-edit the managed block: a rule every host follows, so its home is `CORE_TEMPLATE`, which `clutch core` renders into each host's managed block. This ticket does not change it.
- Bug evidence: a ticket content rule, which "One authoring process" puts only in `clutch/docs/host-authoring.md`. That guide ships in the package and `clutch/author.py` embeds it in the Author prompt, so it is the copy hosts and the Author stage read; `docs/how-clutch-works.md` does not ship. The row's `host-authoring.md:88-92` is therefore the home, not a restatement, and is dropped from the edits.
- Unit and integration suites: `clutch/docs/host-authoring.md` `## Unit and integration tests`, made the one home by `unit-test-io-rule-one-home`. The flaky-test and coverage-threshold rules live in `clutch/specs/implement.md`. The specs keep their restatements because the model needs them.

When this ticket is done, each of the four locations names or links its rule's home and no longer states the rule itself, and no spec, conduct file, or home changes.

## Scope in / Scope out
In (line wrapping of changed text is free):
- `clutch/docs/host-contract.md`, section `## Managed conduct and ticket ownership`: replace the sentence "Do not hand-edit the core: `clutch core` inserts or refreshes it, then commit the routed files." with "Changes to the block follow its own `Engine conduct` rule: `clutch core` inserts or refreshes it, then commit the routed files." Nothing else in the file changes.
- `docs/how-clutch-works.md`, section 3.2 Intake: replace the bullet item 2 of Goal / Why names with the one bullet "- Bug evidence is checked as the authoring guide's [Evidence](../clutch/docs/host-authoring.md#evidence) section states."
- `docs/how-clutch-works.md`, section 4.2 Implement: replace the paragraph from "The Implement prompt separates unit and integration suites." to "an unmet gate requires `premise_failed`." with "The Implement prompt also carries its test rules: suite placement, flaky tests, and coverage thresholds and test time budgets. The unit and integration suites are defined in the authoring guide's [Unit and integration tests](../clutch/docs/host-authoring.md#unit-and-integration-tests) section."
- `docs/how-clutch-works.md`, section 5.2 Bug tickets: replace the sentence that names the authoring guide's path and ends "explains the protocol for authors." with "The authoring guide's [Bug tickets](../clutch/docs/host-authoring.md#bug-tickets) section explains the protocol for authors, and its [Evidence](../clutch/docs/host-authoring.md#evidence) subsection says which ticket reads refuse a bug without evidence.", and delete the three sentences item 3 of Goal / Why names. The first sentence of the section and "The Check gate still verifies the regression proof." stay.
- Nothing else in `docs/how-clutch-works.md` changes, and no heading in either document changes: `clutch/help.py` and `clutch/docs/host-contract.md` link to headings by anchor.
- `tests/integration/test_unit_io_rule.py::test_rule_copies_allow_only_tmp_path_disk`: this is the one test that pins a removed sentence. Drop the phrase "read and write disk only under `tmp_path`, never read or write a repo file, start a process, or open a network connection, and run in milliseconds" from the phrases it requires in `docs/how-clutch-works.md`, and reword the comment above that loop to speak of one documentation location. The `Tests live in` phrase, both forbidden old-ban phrases, the spec checks, and `test_authoring_guide_states_unit_test_io_rule` stay unchanged.

Out:
- `clutch/docs/host-authoring.md`: the home of the bug-evidence and unit-test rules, unchanged. `plan-drain-author-in-parallel` (merged 2026-11-17) edited its `Time budget` bullet; this ticket does not touch the file.
- `clutch/hostfiles.py` and `CORE_TEMPLATE`, `CLAUDE.md`, `AGENTS.md`, and every managed block.
- `clutch/specs/*.md`: specs keep the restatements the model needs.
- The rest of `docs/how-clutch-works.md`: section 2 (`cli-help-standard` edits the 2.1 verb table; the unit-suite parenthetical in 2.2 is not in the row and is filed to the Suggestion Box), section 12, the 4.2 paragraph on assertions that follows the replaced one, and the 3.2 paragraph on Regression and coverage-floor checks.
- `README.md` (`readme-host-first` fences it), `clutch/docs/host-running.md`, and `docs/roadmap.md` (roadmap row 122's audit removes fixed section 2.5 items).
- No new test: the owner treats a standing test of document wording as gold plating. The criteria below are read and grepped.

Merge order: `cli-help-standard` (confirmed, unmerged) also fences `docs/how-clutch-works.md`, but adds only one `help` row to the section 2.1 verb table, more than 50 lines above this ticket's first hunk in section 3.2, and changes nothing in sections 3 to 5. In either order both rebase cleanly. Its criterion 8 grep for a line starting `| ` then `help` is unaffected, because no line this ticket writes starts with `|`, and this ticket's test reads only section 2.2 text that `cli-help-standard` leaves alone. `readme-host-first` (running) fences only `README.md`, which this ticket does not touch.

## Scope fence
- clutch/docs/host-contract.md
- docs/how-clutch-works.md
- tests/integration/test_unit_io_rule.py

## Acceptance criteria
1. `grep -c "hand-edit" clutch/docs/host-contract.md` prints `0`, and the section `## Managed conduct and ticket ownership` names the block's `Engine conduct` rule and still says `clutch core` inserts or refreshes the block and the routed files are committed, which a reader can check there. Ruled out: a contract that keeps its own wording of the rule, or one that drops the `clutch core` step.
2. `grep -c "Every ticket read" docs/how-clutch-works.md` prints `0`, and `grep -c "host-authoring.md#evidence" docs/how-clutch-works.md` prints `2`: one link in section 3.2 and one in section 5.2. Ruled out: a document that still lists which reads refuse a bug, in either section.
3. `grep -c "run in milliseconds" docs/how-clutch-works.md` prints `0`, and section 4.2 holds the link `../clutch/docs/host-authoring.md#unit-and-integration-tests`, which `grep -c "host-authoring.md#unit-and-integration-tests" docs/how-clutch-works.md` counts as `1`. Ruled out: section 4.2 keeping its own copy of the unit-test rule.
4. Each new link resolves to a heading of `clutch/docs/host-authoring.md` (`### Evidence`, `## Bug tickets`, `## Unit and integration tests`), which a reader can check, and `./dev.py test tests/unit/test_help.py tests/integration/test_help.py` exits 0 because no heading of the two edited documents changed. Ruled out: a link to an anchor the guide does not have.
5. `./dev.py test tests/integration/test_unit_io_rule.py` exits 0 with both forbidden old-ban phrases and the spec checks still asserted. Ruled out: a test that passes because its forbidden-phrase loop or spec loop was deleted.
6. `./dev.py test` exits 0.

## Verification
```
./dev.py test tests/integration/test_unit_io_rule.py tests/unit/test_help.py tests/integration/test_help.py
./dev.py test
```

## Definition of rejected
The branch is rejected if it changes a file outside `## Scope fence`; changes any heading of `docs/how-clutch-works.md` or `clutch/docs/host-contract.md`; deletes or rewords text in either document beyond the replacements named in Scope in; states a cited rule again in other words; adds a test that pins document wording; or removes from `tests/integration/test_unit_io_rule.py` more than the one section 4.2 phrase and its comment wording.

## Time budget
- expected: 8m
- stuck: 16m
