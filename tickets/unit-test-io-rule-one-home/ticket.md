---
state: confirmed
source: human
priority: P1
kind: chore
---

## Depends on
- none

## Context
- clutch/docs/host-authoring.md
- clutch/testguard.py::_guards
- tests/integration/test_spec_unit_io_seam.py
- tests/unit/test_specs.py::test_spec_lint_accepts_the_implement_and_requisition_specs
- tests/unit/test_specs.py::test_implement_spec_consumer_read
- tests/unit/test_specs.py::test_review_spec_read_only
- tests/unit/test_specs.py::test_review_spec_checks_docs
- tests/integration/test_stages.py::test_implement_check_review_all_ok_with_artifacts_and_provenance

## On-demand
- clutch/specs/implement.md
- clutch/specs/review.md
- clutch/specs/retro.md
- docs/how-clutch-works.md
- tests/integration/test_retro.py

## Goal / Why
Suggestion Box messages `box-000477` and `box-000484` report that the engine's copies of the unit-test I/O rule disagree, and that the authoring guide states none of them.

- `clutch/specs/requisition_review.md` (two `## Task` bullets, from `requisition-review-unit-disk-read` and `unit-criteria-disk-snag`) lets a `tests/unit/` test use `tmp_path`: "A test reading only `tmp_path` is not a hit", and it snags only a write "outside `tmp_path`", a process, or a network connection.
- `clutch/specs/implement.md` says a unit test "never reads or writes disk", `clutch/specs/review.md` snags "a unit test that reads or writes disk" as `logic`, `clutch/specs/retro.md` files a `unit-io` test repair when "a unit test touches disk", and `docs/how-clutch-works.md` says `tests/unit/` has "no disk" (section 2.2) and that unit tests "avoid disk" (section 4.2). None of these allows `tmp_path`.
- Five merged unit files already use `tmp_path` (`tests/unit/test_journal_ts_under_lock.py`, `test_verdict_submitted_message.py`, `test_parse_ticket_evidence.py`, `test_runner_dead_dependents.py`, `test_intake_plan.py`). `clutch/testguard.py::_guards` blocks process and network calls in the unit suite but nothing on disk, so they pass.

So requisition review can approve a ticket whose new unit test uses `tmp_path`, and then Implement replies `premise_failed` or Review snags it as `logic`: the approve-then-fail loop of `box-000441` and `box-000442`. Separately, the unit/integration placement rule and the floored-file seam road live only in reviewer and implementer prompts. `clutch/docs/host-authoring.md`, which `CLAUDE.md` "One authoring process" makes the one home of ticket content rules and which the Author stage embeds, says nothing about them, so authors learn the rule from a requisition snag (`drain-loop-prompt`, `vscode-help`).

The owner chose the box report's option (a): a unit test may read and write disk only under `tmp_path`, and never touches a repo file, a process, or the network. After this change the authoring guide states that rule and the floored-file seam road once, in a new section, and every other copy says the same thing. `requisition_review.md` and `diagnose.md` already agree and stay unchanged.

## Scope in / Scope out
Scope in (line wrapping of the new text is free; the tests compare whitespace-normalized text):
- `clutch/docs/host-authoring.md`: add a new section headed `Unit and integration tests` (a level-2 Markdown heading, like `Keeping tickets apart`) between the `Keeping tickets apart` section and the `Path matching` section. Its body is these two paragraphs, verbatim:
  - Paragraph 1: "A test under `tests/unit/` reads and writes disk only under `tmp_path`; it never reads or writes a repo file, starts a process, or opens a network connection. In the unit suite `clutch.testguard` blocks processes and network connections but not disk, so reviewers check the disk part. Place a test that needs a repo file, a process, or the network under `tests/integration/` and fence that file. A test using only `tmp_path`, in-memory buffers, or fakes stays under `tests/unit/`, as does a test that reaches a repo file only through an injected seam or fake. Updating a pinned value in an existing unit test that already reads a repo file does not move that test."
  - Paragraph 2: "When Scope in adds lines to a file with a floor above 0 under `[coverage.files]` in `test-gate.toml`, a fenced `tests/unit/` test runs those lines. When running those lines needs a repo file, a process, or the network, Scope in names an in-fence seam, such as an injected reader or a parameter carrying the bytes, through which a fenced `tests/unit` test runs those lines with a fake, and moves only the real disk, process, or network checks to `tests/integration/`. No seam is required for an I/O site where Scope in adds no line."
  Nothing else in the guide changes.
- `clutch/specs/implement.md`, in `## Task`: replace the sentence "It never reads or writes disk, opens a network connection or starts a process, and it runs in milliseconds." with "It reads and writes disk only under `tmp_path`; it never reads or writes a repo file, starts a process, or opens a network connection, and it runs in milliseconds." Bump `version` to the next minor above its value on main at the base commit (`2.13` when drafted, so the major stays `2`).
- `clutch/specs/review.md`, in the `logic` bullet: "a unit test that reads or writes disk, opens a network connection" becomes "a unit test that reads or writes disk outside `tmp_path`, opens a network connection"; the rest of the bullet is unchanged. A repo file is disk outside `tmp_path`, and the existing Admissibility paragraph already keeps Review from blocking on a pinned-value edit in an existing unit test that reads a repo file. Bump `version` to the next minor above its value on main at the base commit (`1.5` when drafted).
- `clutch/specs/retro.md`, in `## Task`: the `unit-io` bullet's "a unit test touches disk, network or a real process" becomes "a unit test touches disk outside `tmp_path`, network or a real process"; the rest of the bullet is unchanged. Bump `version` to the next minor above its value on main at the base commit (`1.4` when drafted).
- `docs/how-clutch-works.md`, these two statements only:
  - Section 2.2: "Tests live in `tests/unit/` (no disk, network or process; run under `clutch.testguard`)" becomes "Tests live in `tests/unit/` (disk only under `tmp_path`, no network or process; run under `clutch.testguard`)".
  - Section 4.2: "Unit tests use fakes for clock, filesystem, processes and network, avoid disk, network and processes, and run in milliseconds." becomes "Unit tests use fakes for clock, filesystem, processes and network, read and write disk only under `tmp_path`, never read or write a repo file, start a process, or open a network connection, and run in milliseconds."
- `tests/unit/test_specs.py`, existing assertions only, with no new test:
  - `test_spec_lint_accepts_the_implement_and_requisition_specs`: the `implement` pin becomes the bumped version; the `requisition_review` and `diagnose` pins stay as they are.
  - `test_implement_spec_consumer_read`: the version pin becomes the bumped implement version, and the pinned rule "A unit test checks one unit with fakes for the clock, filesystem, processes and network. It never reads or writes disk, opens a network connection or starts a process, and it runs in milliseconds." becomes "A unit test checks one unit with fakes for the clock, filesystem, processes and network. It reads and writes disk only under `tmp_path`; it never reads or writes a repo file, starts a process, or opens a network connection, and it runs in milliseconds."
  - `test_review_spec_read_only`: the version pin becomes the bumped review version, and the pinned `logic` phrase becomes "a unit test that reads or writes disk outside `tmp_path`, opens a network connection, starts a process, or depends on wall-clock time or test order".
  - `test_review_spec_checks_docs`: the version pin becomes the bumped review version.
- `tests/integration/test_stages.py::test_implement_check_review_all_ok_with_artifacts_and_provenance`: `review.spec_version == "1.5"` becomes the bumped review version, and `"- spec: implement 2.13"` becomes the bumped implement version. No other line in this file changes, and no test is added to it (it is on the do-not-grow list).
- `tests/integration/test_retro.py`: the `"spec_version": "1.4"` provenance pin becomes the bumped retro version. No other line changes.
- Create `tests/integration/test_unit_io_rule.py` with the two tests named in the acceptance criteria. It reads repo files, so it lives under `tests/integration/`. Each test collapses whitespace with `" ".join(text.split())` before checking substrings.

Scope out:
- `clutch/specs/requisition_review.md` stays unchanged. Its two unit I/O bullets already state the chosen rule: the repo-file read snag says "A test reading only `tmp_path` is not a hit", and the write, process, and network snag fires only on a write "outside `tmp_path`" and carries the floored-file seam road. The new guide section reuses their wording. `tests/integration/test_requisition.py` and `tests/integration/test_spec_unit_io_seam.py` stay unchanged.
- `clutch/specs/diagnose.md` stays unchanged: its lesson rule keeps floored lines reachable from `tests/unit/` and already matches the guide.
- `clutch/testguard.py` stays unchanged. It blocks only process and network calls, which matches the guide's statement that reviewers check the disk part. No engine lint, gate, or guard code is added for the disk rule.
- `clutch/specs/author.md` stays unchanged: it embeds the guide whole, so the new section reaches the Author stage without a spec edit.
- Existing `tests/unit/` files that already read repo files (for example `tests/unit/test_specs.py`) stay where they are.
- No test that compares the copies of the rule for equality: that is the cause fix tracked by `box-000474`, routed through triage.
- `CLAUDE.md`, `AGENTS.md`, `clutch/hostfiles.py`, `clutch/docs/host-contract.md` and `docs/how-clutch-works.md` section 12 (whose `clutch.testguard` bullet already says it blocks process and network IO) stay unchanged.
- No existing ticket is edited.

## Scope fence
- clutch/docs/host-authoring.md
- clutch/specs/implement.md
- clutch/specs/review.md
- clutch/specs/retro.md
- docs/how-clutch-works.md
- tests/unit/test_specs.py
- tests/integration/test_stages.py
- tests/integration/test_retro.py
- tests/integration/test_unit_io_rule.py

## Acceptance criteria
1. `tests/integration/test_unit_io_rule.py::test_authoring_guide_states_unit_test_io_rule` passes. It asserts that `clutch/docs/host-authoring.md` has a line `## Unit and integration tests` that comes after `## Keeping tickets apart` and before `## Path matching`, and that the whitespace-normalized guide contains each of these phrases. It fails if any one phrase is removed:
   - "A test under `tests/unit/` reads and writes disk only under `tmp_path`; it never reads or writes a repo file, starts a process, or opens a network connection."
   - "`clutch.testguard` blocks processes and network connections but not disk"
   - "Place a test that needs a repo file, a process, or the network under `tests/integration/` and fence that file."
   - "A test using only `tmp_path`, in-memory buffers, or fakes stays under `tests/unit/`, as does a test that reaches a repo file only through an injected seam or fake."
   - "Updating a pinned value in an existing unit test that already reads a repo file does not move that test."
   - "When Scope in adds lines to a file with a floor above 0 under `[coverage.files]` in `test-gate.toml`, a fenced `tests/unit/` test runs those lines."
   - "When running those lines needs a repo file, a process, or the network, Scope in names an in-fence seam, such as an injected reader or a parameter carrying the bytes, through which a fenced `tests/unit` test runs those lines with a fake, and moves only the real disk, process, or network checks to `tests/integration/`."
   - "No seam is required for an I/O site where Scope in adds no line."
   Ruled out: today's guide, which states no placement rule, and a guide that bans all disk in unit tests.
2. `tests/integration/test_unit_io_rule.py::test_rule_copies_allow_only_tmp_path_disk` passes. After whitespace normalization it asserts:
   - the `## Task` section of `clutch/specs/implement.md` (the body between `## Task\n` and `## Inputs\n` of `load_spec(text).body`) contains "It reads and writes disk only under `tmp_path`; it never reads or writes a repo file, starts a process, or opens a network connection" and does not contain "It never reads or writes disk";
   - the `## Task` section of `clutch/specs/review.md` contains "a unit test that reads or writes disk outside `tmp_path`, opens a network connection" and does not contain "a unit test that reads or writes disk, opens";
   - the `## Task` section of `clutch/specs/retro.md` contains "`unit-io`: a unit test touches disk outside `tmp_path`, network or a real process" and does not contain "a unit test touches disk, network";
   - `docs/how-clutch-works.md` contains "Tests live in `tests/unit/` (disk only under `tmp_path`, no network or process; run under `clutch.testguard`)" and "read and write disk only under `tmp_path`, never read or write a repo file, start a process, or open a network connection, and run in milliseconds", and contains neither "no disk, network or process" nor "avoid disk, network and processes".
   Ruled out: today's copies, which ban `tmp_path`, and a copy that adds the new text but keeps the old sentence beside it.
3. `./dev.py test tests/unit/test_specs.py` passes with the `implement` pins set to the bumped implement version, the `review` pins set to the bumped review version, each one minor above its value on main at the base commit with the same major (`2.13` and `1.5` when drafted), and the `requisition_review` (`3.17`) and `diagnose` (`1.6`) pins unchanged. `test_implement_spec_consumer_read` pins the new unit-test sentence and `test_review_spec_read_only` pins the new `logic` phrase from Scope in, so each fails against the unedited spec. The edited implement and review specs still lint clean and stay within `SPEC_MAX_LINES`, as the existing assertions in those two tests check. The edited retro spec still loads through `load_spec`, which `tests/integration/test_retro.py` exercises (criterion 4).
4. `./dev.py test tests/integration/test_stages.py -k test_implement_check_review_all_ok_with_artifacts_and_provenance` passes with the review `spec_version` pin and the run-record `spec: implement` pin at the bumped versions. `./dev.py test tests/integration/test_retro.py` passes with the provenance `spec_version` pin at the bumped retro version, one minor above its value on main at the base commit with the same major (`1.4` when drafted).
5. `./dev.py test tests/integration/test_spec_unit_io_seam.py tests/integration/test_requisition.py` passes with both files and `clutch/specs/requisition_review.md` unchanged, which shows the requisition copy of the rule is intact.
6. `./dev.py test tests/unit/test_host_authoring.py tests/integration/test_author.py tests/integration/test_contention_rules.py tests/integration/test_fence_closure_registries.py` exits 0: the Author render still embeds the guide byte for byte, and the new section names no do-not-grow test file and keeps every existing pinned guide phrase.

## Verification
```
./dev.py test tests/integration/test_unit_io_rule.py
./dev.py test tests/unit/test_specs.py
./dev.py test tests/integration/test_stages.py -k test_implement_check_review_all_ok_with_artifacts_and_provenance
./dev.py test tests/integration/test_retro.py
./dev.py test tests/integration/test_spec_unit_io_seam.py tests/integration/test_requisition.py
./dev.py test tests/unit/test_host_authoring.py tests/integration/test_author.py tests/integration/test_contention_rules.py tests/integration/test_fence_closure_registries.py
```

## Definition of rejected
The branch is rejected if:
- it edits any file outside the fence, including `clutch/specs/requisition_review.md`, `clutch/specs/diagnose.md` or `clutch/testguard.py`;
- any edited copy still bans all disk in a unit test, or lets a unit test read or write a repo file, start a process, or open a network connection;
- the guide states the rule in more than the one new section, or changes any existing guide text;
- it adds an engine lint, gate, or guard code path for the disk rule;
- it adds a test to `tests/unit/test_specs.py`, `tests/integration/test_stages.py` or `tests/integration/test_retro.py`, or changes a line there other than the pins Scope in names;
- a new test reads a repo file from under `tests/unit/`;
- either new test still passes after any one of its listed phrases is removed from the file it reads.

## Time budget
- expected: 25m
- stuck: 60m
