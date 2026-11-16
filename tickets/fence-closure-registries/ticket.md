---
state: confirmed
source: human
priority: P1
kind: feature
---

## Depends on
- none

## Context
- clutch/docs/host-authoring.md#What each section is for
- tests/unit/test_specs.py::test_spec_lint_accepts_the_implement_and_requisition_specs
- tests/unit/test_specs.py::test_requisition_review_spec_snags_non_protocol_regression
- tests/integration/test_author.py::test_author_spec_states_ticket_rules

## On-demand
- clutch/specs/requisition_review.md

## Goal / Why
The scope-fence set-membership rule misses in-code registries, and a ticket that adds a registry key passes requisition review with the test that pins that registry left outside its fence.

History: `box-000324` (retro/27) found three rejects (`order-verb`, `ask-prompt-verb`, `specs-in-package`) whose fences left out a test or doc that pins a whole set. `set-membership-fence-closure` (6a30ca57) added one rule for that, word for word, in two places: the `## Task` bullet in `clutch/specs/requisition_review.md` (the reviewer) and the `Scope fence` bullet in `clutch/docs/host-authoring.md` (the authoring guide that chat authors read and the Author stage embeds). The rule's examples name only "CLI subcommand, file or directory path, spec name".

It happened again in `tickets/retro/000046.md` proposal 2. `draft-worth-report` added the `extension_only` entry `clutchAskDrafts` to `clutch/observe.py::MENU`. `tests/integration/test_menu_verb_parity.py::test_menu_matches_verbs` asserts that the `extension_only` subset of `MENU` equals an exact set, and that file was not fenced. Requisition review approved the ticket because it did not count a key in an in-code registry as a member of a set. Implement returned `premise_failed` with all 19 parametrized cases failing (`tickets/draft-worth-report/diagnosis.json`), and Diagnose sent the ticket to the Reject queue.

Owner decision 1 in `docs/roadmap.md` (section 6) is to fix the instructions first: widen the prompt rule to in-code registries and tables now, and run a spike on a mechanical analyzer only if a third escape happens.

When this ticket is done, both copies of the rule say these things:
- An entry of an in-code registry, table, mapping, or closed vocabulary is a set member.
- For such an entry, grep `tests/` for the collection's name.
- Fence every test that compares the collection, or a filtered subset of it, for exact equality or lists it in full.
- Fence every file holding a table that a test requires to match the collection entry for entry.
- A test that only imports or iterates the collection, or reads one entry the change leaves alone, is not a hit. This guard comes from retro proposal 2's overcorrection risk, so fences do not grow to every reader.

Why both files: the guide is where this rule lives for ticket content (CLAUDE.md "One authoring process"), and the reviewer spec holds a copy of it. If only the copy changed, authors would never hear the rule the reviewer snags on.

## Scope in / Scope out
Scope in:
- `clutch/specs/requisition_review.md`, `## Task`: replace the set-membership bullet (the one starting "When Scope in adds, removes, renames, or moves a member of a set") with the text below, as one bullet. Bump frontmatter `version` to the next minor above its value on main at the base commit; the major stays the same. Nothing else in the spec changes.
- `clutch/docs/host-authoring.md`, `Scope fence` bullet under `## What each section is for`: replace the same two sentences (from "When Scope in adds, removes, renames, or moves a member of a set" through "is not a hit.") with the same text. Every other sentence of that bullet and of the guide stays the same. Line wrapping may differ.
- `tests/unit/test_specs.py::test_spec_lint_accepts_the_implement_and_requisition_specs`: change only the `requisition_review` version literal to the new version.
- New file `tests/integration/test_fence_closure_registries.py` with the two tests named in the acceptance criteria. It is under `tests/integration/` because it reads a repo spec and a repo doc.

The replacement text:

> When Scope in adds, removes, renames, or moves a member of a set (CLI subcommand, file or directory path, spec name, or an entry of an in-code registry, table, mapping, or closed vocabulary such as a menu, verb, kind, or adapter table), grep `tests/` and `docs/` for files that list that set or hardcode the old path, and fence every hit that asserts against the changed set or hardcodes the moved path. For an in-code entry, also grep `tests/` for the collection's name, and fence every test that compares that collection or a filtered subset of it for exact equality or lists it in full, and every file holding a table that a test requires to match the collection entry for entry. A mere textual mention, a path built under `tmp_path`, or a historical form the ticket keeps valid is not a hit. A test that only imports or iterates the collection, or reads one entry the change leaves alone, is not a hit.

Scope out:
- Any mechanical fence-closure analyzer, lint, gate, or finding code. Decision 1 puts those off until a third escape.
- `clutch/specs/author.md`. It embeds the guide, and `tests/integration/test_author.py::test_author_spec_requires_criteria_to_name_wrong_results` asserts that the rule is not in its body.
- The `CORE_TEMPLATE` block in `clutch/hostfiles.py`, `CLAUDE.md`, and `AGENTS.md`.
- `docs/how-clutch-works.md`. Its `requisition_review.md` row in the spec table does not list the fence closures, so this change makes nothing in it false.
- Every other spec, and `clutch/requisition.py`.
- Making requisition review embed the guide instead of keeping its own copy. That is a separate cause fix, filed to the Suggestion Box.

Tests outside the fence that read the two edited files, and why each still passes:
- `tests/integration/test_requisition.py::test_spec_loads_and_names_finding_keys` and `::test_requisition_review_spec_snags_unit_test_disk_read` assert phrases from other bullets and the input list, none of which change.
- `tests/integration/test_author.py::test_author_spec_requires_criteria_to_name_wrong_results` checks that "adds, removes, renames, or moves a member of a set" is in the guide and not in `author.md`. That phrase stays.
- `tests/integration/test_author.py::test_author_spec_states_ticket_rules` checks for "asserts against the changed set or hardcodes the moved path" and "A mere textual mention, a path built under `tmp_path`". Both stay verbatim.
- `tests/unit/test_host_authoring.py` asserts seven phrases from other bullets.
- `tests/unit/test_docs_verb.py`, `tests/integration/test_tickets.py::test_new_names_installed_authoring_guide`, and `tests/unit/test_author.py` use only the guide's path or a monkeypatched read.
- `tests/integration/test_author.py::test_author_prompt_contains_guide_and_skeletons` compares the prompt's guide block to the file as it is read at run time, so any guide text passes.

## Scope fence
- clutch/specs/requisition_review.md
- clutch/docs/host-authoring.md
- tests/unit/test_specs.py
- tests/integration/test_fence_closure_registries.py

## Acceptance criteria
1. `tests/integration/test_fence_closure_registries.py::test_requisition_review_spec_traces_in_code_collections` loads and renders `clutch/specs/requisition_review.md` the way `tests/unit/test_specs.py::test_requisition_review_spec_snags_non_protocol_regression` does, takes the whitespace-normalized `## Task` text, and asserts it contains each of these phrases:
   - "an entry of an in-code registry, table, mapping, or closed vocabulary"
   - "grep `tests/` for the collection's name"
   - "compares that collection or a filtered subset of it for exact equality or lists it in full"
   - "every file holding a table that a test requires to match the collection entry for entry"
   - "A test that only imports or iterates the collection, or reads one entry the change leaves alone, is not a hit."
   - "adds, removes, renames, or moves a member of a set"
   - "asserts against the changed set or hardcodes the moved path"
   - "A mere textual mention, a path built under `tmp_path`, or a historical form the ticket keeps valid is not a hit."

   Ruled out: the spec at the base commit, which names only CLI subcommands, paths, and spec names and fails the first phrase; a widened rule without the limit sentence, which fails the fifth; and a rewrite that drops the existing trigger or limit, which fails the last three. `./dev.py test tests/integration/test_fence_closure_registries.py` checks it.
2. `tests/integration/test_fence_closure_registries.py::test_authoring_guide_traces_in_code_collections` reads `clutch/docs/host-authoring.md`, normalizes its whitespace, and asserts it contains the same eight phrases as criterion 1. Ruled out: a change to the reviewer spec alone that leaves the guide naming only CLI subcommands, paths, and spec names. `./dev.py test tests/integration/test_fence_closure_registries.py` checks it.
3. `clutch/specs/requisition_review.md` frontmatter `version` is one minor above its value on main at the base commit (it was "3.15" when this ticket was drafted), with the same major. `tests/unit/test_specs.py::test_spec_lint_accepts_the_implement_and_requisition_specs` pins the new value, and `lint_spec` still returns `[]`. Ruled out: an unbumped spec, which fails the new pin, and a major bump, which changes `produced_by_spec_version`. `./dev.py test tests/unit/test_specs.py` checks it.
4. `./dev.py test tests/integration/test_author.py tests/integration/test_requisition.py tests/unit/test_host_authoring.py` exits 0. This shows that the existing phrases those tests pin in the guide and the spec survive the rewrite.
5. `./dev.py test` exits 0.

## Verification
```
./dev.py test tests/integration/test_fence_closure_registries.py
./dev.py test tests/unit/test_specs.py
./dev.py test tests/integration/test_author.py tests/integration/test_requisition.py tests/unit/test_host_authoring.py
./dev.py test
```

## Definition of rejected
The branch is rejected if:
- only one of the two files gets the widened rule;
- the existing set-membership trigger or the existing limit sentence is weakened or removed;
- the limit for in-code entries is missing, so every test that imports or iterates a registry becomes a hit;
- it adds a mechanical analyzer, a lint rule, a gate, a finding code, or a config knob;
- the spec version is not bumped or its major changes;
- any other spec bullet or guide sentence changes;
- any file outside `## Scope fence` changes.

## Time budget
- expected: 20m
- stuck: 60m
