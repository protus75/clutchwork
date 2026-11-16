---
state: confirmed
source: human
priority: P1
kind: feature
---

## Depends on
- none

## Context
- tests/integration/test_requisition.py::test_requisition_review_spec_snags_unit_test_disk_read
- tests/unit/test_specs.py::test_spec_lint_accepts_the_implement_and_requisition_specs
- tests/unit/test_specs.py::test_diagnose_spec_lesson_length_guidance

## On-demand
- clutch/specs/requisition_review.md
- clutch/specs/diagnose.md

## Goal / Why
Roadmap row 9 (`docs/roadmap.md` section 8, from Suggestion Box messages `box-000441` and `box-000442`). Two halves of it are still open at main.

`requisition-review-unit-disk-read` (merged `414ca359`) added one `## Task` bullet to `clutch/specs/requisition_review.md`. It snags a `tests/unit/` test that a ticket makes read a named repo file, and its only paved road is "place that test under `tests/integration/` and fence that file". Two gaps remain:

1. The bullet says nothing about a unit test made to write disk, start a process, or open a network connection. `clutch/specs/review.md` (the `logic` snag) and `clutch/specs/implement.md` ban all four, so such a ticket still passes requisition review and then fails Implement with `premise_failed`. The first `vscode-help` requisition review raised `unit-test-disk-write` only because that reviewer happened to look.
2. A plain move to integration traps a ticket whose unit test had to run new lines in a floored file. On `drain-loop-prompt`, Diagnose's lesson 2 (`tickets/drain-loop-prompt/diagnosis.json`) said to move the four tests to `tests/integration/` and remove `tests/unit/test_ask_drain_loop.py`. The next requisition reviews then snagged `coverage-floor-lines-unrun` eight times, because the floor bullet still needs a fenced `tests/unit` test to run the new lines in `clutch/ask.py` (floor 25) and `clutch/__main__.py` (floor 13), and those lines read disk directly. `clutch/specs/diagnose.md` has no rule against such a lesson.

Triage tombstoned `box-000442` against `requisition-review-unit-disk-read`, but that ticket merged without the seam road or the Diagnose rule.

After this change:
- Requisition review also snags a unit test made to write disk, start a process, or open a network connection.
- When either unit I/O snag hits a test that must run new lines in a floored file, its paved road names an in-fence seam, so a unit test can run those lines with a fake. Only the real I/O checks move to integration.
- Diagnose never writes a re-scope lesson that leaves a floored file's new lines unreachable from `tests/unit/`.

Measure the effect in later retros: fewer Implement `premise_failed` findings that cite the unit I/O rule, and no `coverage-floor-lines-unrun` snag right after a Diagnose re-scope lesson.

## Scope in / Scope out
Scope in:
- In `clutch/specs/requisition_review.md`, insert one new bullet into the `## Task` list directly after the existing bullet that begins "When a criterion or `## Verification` line names a `tests/unit/` file whose test the ticket adds". Use this text verbatim (line wrapping is free, since the tests compare whitespace-normalized text):
  "When a criterion, a test Scope in adds, or a `## Verification` line makes a `tests/unit/` test write disk outside `tmp_path`, start a process, or open a network connection, raise a `snag` finding: place that test under `tests/integration/` and fence that file. When this snag or the repo-file snag above hits a test that must run new lines in a file with a floor above 0 under `[coverage.files]`, its paved road also names an in-fence seam, such as an injected reader or a parameter carrying the bytes, through which a fenced `tests/unit` test runs those lines with a fake, and moves only the real disk, process, or network checks to `tests/integration/`. A test using only in-memory buffers or fakes is not a hit. No seam is required for an I/O site where Scope in adds no line."
- The existing repo-file bullet stays byte-for-byte unchanged, so `tests/integration/test_requisition.py::test_requisition_review_spec_snags_unit_test_disk_read` keeps passing untouched.
- In `clutch/specs/diagnose.md`, add one paragraph to `## Task` directly after the paragraph that ends "drop prose around them instead.". Use this text verbatim (wrapping free):
  "When a lesson moves a test out of `tests/unit/` and that test must run lines the ticket adds to a file with a floor above 0 under `[coverage.files]` in `test-gate.toml`, the lesson keeps those lines reachable from `tests/unit/`: it names that file and the I/O call there that needs an in-fence seam, such as an injected reader or a parameter carrying the bytes, so a unit test runs those lines with a fake, and it moves only the real disk, process, or network checks to `tests/integration/`. Never tell the author to drop unit coverage of those lines."
  The sentence names a file and an I/O call that the ticket or merged code states, so it agrees with the existing rule against naming a mechanism neither one states.
- Bump the `version` of `clutch/specs/requisition_review.md` and of `clutch/specs/diagnose.md`, each to the next minor above its version on main.
- In `tests/unit/test_specs.py`, update only the `requisition_review` and `diagnose` version pins in the tuple in `test_spec_lint_accepts_the_implement_and_requisition_specs`. Leave the `implement` pin and every other line unchanged, and add no new test to this file.
- Create `tests/integration/test_spec_unit_io_seam.py` with two tests. Each reads the spec from `Path(__file__).resolve().parents[2] / "clutch" / "specs"`, takes `load_spec(text).body` between `## Task\n` and `## Inputs\n`, collapses whitespace with `" ".join(...split())`, and asserts every phrase listed in its criterion is a substring. Both tests are new, and they go under `tests/integration/` because they read repo files.

Scope out:
- `clutch/specs/review.md`, `clutch/specs/implement.md`, `clutch/specs/author.md`, `clutch/docs/host-authoring.md`, `clutch/tickets.py` lint, `clutch/testguard.py`, and `tests/integration/test_requisition.py` stay unchanged.
- No engine code changes. The rules live only in the two prompt specs.
- `docs/how-clutch-works.md` stays unchanged. Its section 8.4 row for `requisition_review.md` and its section 6.3 Diagnose summary list no individual snag or lesson rule, so neither becomes false.
- No existing ticket is edited.

## Scope fence
- clutch/specs/requisition_review.md
- clutch/specs/diagnose.md
- tests/integration/test_spec_unit_io_seam.py
- tests/unit/test_specs.py

## Acceptance criteria
1. `tests/integration/test_spec_unit_io_seam.py::test_requisition_review_spec_snags_unit_io_with_seam_road` passes. It asserts that the whitespace-normalized `## Task` of `clutch/specs/requisition_review.md` contains each of these six phrases, and it fails if any one is removed from the spec:
   - "makes a `tests/unit/` test write disk outside `tmp_path`, start a process, or open a network connection, raise a `snag` finding: place that test under `tests/integration/` and fence that file"
   - "hits a test that must run new lines in a file with a floor above 0 under `[coverage.files]`"
   - "its paved road also names an in-fence seam, such as an injected reader or a parameter carrying the bytes, through which a fenced `tests/unit` test runs those lines with a fake"
   - "moves only the real disk, process, or network checks to `tests/integration/`"
   - "A test using only in-memory buffers or fakes is not a hit."
   - "No seam is required for an I/O site where Scope in adds no line."
   Ruled out: a spec that snags only repo-file reads (today's text), and a seam road that leaves out the floored-file condition.
2. `tests/integration/test_spec_unit_io_seam.py::test_diagnose_spec_keeps_floored_lines_unit_reachable` passes. It asserts that the whitespace-normalized `## Task` of `clutch/specs/diagnose.md` contains each of these four phrases, and it fails if any one is removed from the spec:
   - "When a lesson moves a test out of `tests/unit/` and that test must run lines the ticket adds to a file with a floor above 0 under `[coverage.files]` in `test-gate.toml`"
   - "the lesson keeps those lines reachable from `tests/unit/`: it names that file and the I/O call there that needs an in-fence seam, such as an injected reader or a parameter carrying the bytes"
   - "it moves only the real disk, process, or network checks to `tests/integration/`"
   - "Never tell the author to drop unit coverage of those lines."
   Ruled out: today's `diagnose.md`, which has no such rule.
3. `./dev.py test tests/integration/test_requisition.py -k unit_test_disk_read` passes with `tests/integration/test_requisition.py` unchanged, which shows the existing repo-file bullet and its three guard clauses are intact.
4. `tests/unit/test_specs.py::test_spec_lint_accepts_the_implement_and_requisition_specs` passes with the `requisition_review` pin set to the bumped version (the next minor above main's `3.15` at authoring time) and the `diagnose` pin set to its bumped version (the next minor above main's `1.5` at authoring time). Each pin fails against the unbumped spec. Both specs still lint clean and stay within `SPEC_MAX_LINES`.
5. `./dev.py test tests/unit/test_specs.py tests/integration/test_diagnose_eval.py tests/integration/test_requisition.py` exits 0. Both specs still load and render through the production paths those files exercise.

## Verification
```
./dev.py test tests/integration/test_spec_unit_io_seam.py
./dev.py test tests/integration/test_requisition.py -k unit_test_disk_read
./dev.py test tests/unit/test_specs.py tests/integration/test_diagnose_eval.py tests/integration/test_requisition.py
```

## Definition of rejected
The branch is rejected if:
- it edits any file outside the fence;
- it changes the text of the existing repo-file bullet in `requisition_review.md`;
- the new requisition bullet asks for a seam at an I/O site where Scope in adds no line, or flags a unit test that uses only in-memory buffers or fakes;
- the Diagnose rule lets a lesson drop unit coverage of a floored file's new lines;
- it adds an engine lint, gate, or code path for this rule;
- a new test reads a repo file from under `tests/unit/`;
- either new test still passes after any one of its listed phrases is removed from the spec.

## Time budget
- expected: 20m
- stuck: 50m
