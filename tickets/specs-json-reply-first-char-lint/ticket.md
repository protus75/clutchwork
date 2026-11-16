---
state: draft
source: box:suggestion
priority: P1
kind: feature
agent_tier: medium
agent_effort: medium
---

## Depends on
- diagnose-spec-first-char-json-reply

## Context
- clutch/specs/__init__.py::_parse_spec
- tests/unit/test_specs.py::spec_text

## On-demand
- clutch/specs/author.md
- clutch/specs/triage.md
- clutch/specs/rework.md
- clutch/specs/retro.md
- clutch/specs/implement.md
- tests/integration/test_rework.py

## Goal / Why
Every JSON-reply prompt spec tells the model that its reply starts with the object, and `lint_spec` refuses a spec that does not. Today only `requisition_review.md` and `review.md` say so. `Driver` rejects a reply with prose before the JSON (`unwrap_fence` strips only a fence around the whole reply), and each rejection is a paid re-prompt. Saved replies since 2026-11-09 show 21 of 224 author replies and 6 of 13 rework replies starting with prose. When the re-prompts run out, a surface falls back to a mechanical outcome (for Diagnose, `abandon-human`, which can send a buildable ticket to the Reject queue). The sentence was patched one spec at a time. After the sentence, requisition fell from 8.3% to 2.3% prose-first replies and review from 8.8% to 2.7%. A lint finding is the cause fix: a new or edited JSON-reply spec cannot ship without the rule. The success measure after merge is the author and rework prose-first rate in `<state_dir>/spools/`, which should fall toward the requisition/review rate.

## Scope in / Scope out
In:
- `clutch/specs/__init__.py`: in `_parse_spec`, add a finding with code `spec_json_reply`. It fires when the `## Output format` section text contains `JSON object` and does not match the regex `first (non-whitespace )?character of your reply`. Its paved road names the sentence to add: "The first character of your reply is `{` and the last is `}`; no prose, markdown or code fence surrounds the object." The regex accepts the two wordings already on main (`requisition_review.md`, `review.md`; `review.md` deliberately allows one json fence, so its wording stays). The check needs no new import beyond `re`, which the module already uses.
- Append that sentence to a named line in the `## Output format` section of each spec: the line starting `Reply with ONLY one JSON object` in `author.md` and `triage.md`; the line containing `reply with ONLY` (about line 117) in `implement.md`; the last prose line of the section in `retro.md` (about line 60, the one beginning `Each proposal may also include` and mentioning `recurs`); and the last prose line in `rework.md` (about line 85, ending `Proposal objects allow only `stem` and `ticket`.`). Do not append to the earlier lines that end with a colon or introduce a list or JSON shape (`retro.md` about line 56, `rework.md` about line 79). Keep every other line of those specs and their `version` unchanged.
- `tests/integration/test_rework.py`: exactly one edit, updating the golden sha256 of the rendered `rework.md` (about line 456) to the new render hash. Its version pin `1.1` (about line 452) stays unchanged.
- `tests/unit/test_specs.py`: the `spec_text` helper's `## Output format` body (`One JSON object.`) gains the sentence so `lint_spec(spec_text()) == []` still holds. This is the one expectation that may change; no other edit there.
- New `tests/unit/test_specs_json_reply_rule.py` holds the in-memory tests (criteria 1, 2, 4). New `tests/integration/test_specs_json_reply_specs.py` holds the tests that read the real spec files (criteria 3, 5).
Out: `clutch/specs/diagnose.md` (the sentence is added by the `diagnose-spec-first-char-json-reply` ticket this one depends on), `review.md`, `requisition_review.md`, the `clutch/specs/ask/` templates (not JSON-reply specs, not run through `lint_spec`), spec versions, and any change to `Driver` or `unwrap_fence`.

## Scope fence
- clutch/specs/__init__.py
- clutch/specs/author.md
- clutch/specs/triage.md
- clutch/specs/rework.md
- clutch/specs/retro.md
- clutch/specs/implement.md
- tests/unit/test_specs.py
- tests/unit/test_specs_json_reply_rule.py
- tests/integration/test_specs_json_reply_specs.py
- tests/integration/test_rework.py

## Acceptance criteria
1. `./dev.py test tests/unit/test_specs_json_reply_rule.py` has a test that `lint_spec` on `spec_text`-style text whose `## Output format` says `One JSON object.` without the sentence returns a finding with code `spec_json_reply` and a non-empty `paved_road`, not `[]`.
2. The same file has a test that the text with the sentence `The first character of your reply is `{` and the last is `}`` added lints to `[]`, and that the `review.md` wording (`The first non-whitespace character of your reply is ...`) also lints to `[]`, so the rule does not demand one fixed wording.
3. `tests/integration/test_specs_json_reply_specs.py` has a test that loops over every `clutch/specs/*.md` (not `ask/`) and asserts `lint_spec(text) == []`, so a spec that drops the sentence fails; and a test that removing the sentence from the real `author.md` text yields a `spec_json_reply` finding, not `[]`.
4. A test in `tests/unit/test_specs_json_reply_rule.py` asserts that text whose `## Output format` has no `JSON object` and no sentence yields no `spec_json_reply` finding (the rule does not hit non-JSON specs).
5. `author.md`, `triage.md`, `rework.md`, `retro.md` and `implement.md` each contain the sentence inside `## Output format`, not in `## Task` or `## On-failure`; a test in `tests/integration/test_specs_json_reply_specs.py` checks the section text of each and fails if one is missing.
6. `./dev.py test tests/unit/test_specs.py tests/integration/test_requisition.py tests/integration/test_author.py tests/integration/test_rework.py` exits 0, so the updated rework golden hash, the existing spec version pins and the line budget (`SPEC_MAX_LINES`) hold.

## Verification
```
./dev.py test tests/unit/test_specs_json_reply_rule.py tests/integration/test_specs_json_reply_specs.py tests/unit/test_specs.py tests/integration/test_requisition.py tests/integration/test_author.py tests/integration/test_rework.py
```

## Definition of rejected
The branch is thrown away if `Driver`, `unwrap_fence` or any file outside the fence changes, if `tests/integration/test_rework.py` changes beyond the golden sha256, if a spec `version` changes, if `review.md` is reworded to drop its json-fence allowance, if the lint hard-codes one exact sentence so `review.md` or `requisition_review.md` fails, or if a test passes when the sentence is removed from a spec.

## Time budget
- expected: 40m
- stuck: 90m
