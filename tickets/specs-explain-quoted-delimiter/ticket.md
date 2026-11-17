---
state: draft
source: box:suggestion
priority: P1
kind: feature
agent_tier: medium
agent_effort: medium
---

## Depends on
none

## Context
- clutch/specs/__init__.py::quote_payload
- clutch/specs/__init__.py::render

## Goal / Why
Every rendered stage prompt tells the model that `[clutch-data:` inside a data block stands for the real data-block delimiter in the file on disk. Today `quote_payload` rewrites every delimiter in a payload to `[clutch-data:`, and no stage spec says so. On 2026-11-17 `estimate-calibration-author` attempt 0 ended `premise_failed` for this reason. Its criterion 4 greps `clutch/specs/author.md` for the real delimiter, and the implementer saw the quoted form in the embedded ticket and judged the criterion wrong. Diagnose found the ticket correct on disk. Any ticket that edits a spec's Inputs or names the delimiter can bounce the same way, and a premise bounce can send a buildable ticket to the Reject queue.

## Scope in / Scope out
Scope in: add one sentence to the `## Role` section of each of the nine engine stage specs: `acceptance`, `author`, `diagnose`, `implement`, `requisition_review`, `retro`, `review`, `rework` and `triage`. The sentence says that `[clutch-data:` in any data block is the renderer's quoting of the real delimiter, which is two less-than signs followed by `clutch-data:` in the file on disk, and that a ticket or text naming the delimiter is correct as written and is never an error or a false premise. Spell the real delimiter in words, never raw, because the spec lint refuses a raw delimiter outside a begin/end line. No spec `version` is bumped (the sentence adds no new input or output rule), so no version pin changes. Add a new integration test file that checks the sentence in every spec and renders a fixture payload.
Scope out: `clutch/specs/__init__.py` and the quoting behavior, `clutch/specs/ask/*`, the plan document, and every other spec section.

## Scope fence
- clutch/specs/acceptance.md
- clutch/specs/author.md
- clutch/specs/diagnose.md
- clutch/specs/implement.md
- clutch/specs/requisition_review.md
- clutch/specs/retro.md
- clutch/specs/review.md
- clutch/specs/rework.md
- clutch/specs/triage.md
- tests/integration/test_specs_delimiter_note.py

## Acceptance criteria
1. For each of the nine spec names above, `./dev.py test tests/integration/test_specs_delimiter_note.py` loads the spec with `load_spec` and asserts its `## Role` section contains both `[clutch-data:` and the phrase `two less-than signs`. A spec lacking the sentence fails the test; the test does not pass on an empty or missing Role.
2. The same test renders each spec through `render` with every input set to a payload that contains the real delimiter (built as `DATA_DELIM + "begin x>>"`). It asserts the rendered prompt contains the Role sentence and contains `[clutch-data:begin x>>`, and does not contain `DATA_DELIM + "begin x>>"` inside that payload. `render` must not raise `SpecError`.
3. `lint_spec` returns `[]` for each of the nine specs after the edit, checked by `./dev.py test tests/unit/test_specs.py tests/integration/test_specs_delimiter_note.py`. The result is not a `data_block` or `spec_size` finding.
4. No `version:` frontmatter value changes in any of the nine specs, checked by the same test reading `meta.version` against the values the existing pinned tests already assert (`./dev.py test tests/unit/test_specs.py tests/integration/test_author.py`).

## Verification
```
./dev.py test tests/integration/test_specs_delimiter_note.py tests/unit/test_specs.py tests/integration/test_author.py tests/integration/test_acceptance_spec.py
```

## Definition of rejected
A spec spells the raw delimiter in its Role text. A `version` bump. A change to `quote_payload` or any file outside the fence. A new test added to an existing hot test file.

## Time budget
- expected: 15m
- stuck: 30m
