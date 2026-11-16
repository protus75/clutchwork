---
priority: P2
kind: chore
agent_tier: medium
agent_effort: medium
source: box:roadmap_row
state: rejected
---

## Depends on
none

## Context
- docs/roadmap.md#2.2 Closed sets with more than one home
- docs/roadmap.md#2.3 Repeated helpers and projections
- clutch/artifacts.py::NonBlank
- clutch/artifacts.py::_Strict
- clutch/stages.py::_major
- clutch/tickets.py::_repo_path
- clutch/covgate.py
- clutch/policy.py
- clutch/llm.py
- tests/integration/test_closed_sets.py

## Goal / Why
Today the tier, priority and kind vocabularies are spelled out in several modules, and `__main__.py` hard-codes `("feature", "bug", "chore")` and `("P0", "P1", "P2", "P3")` as argparse choices. Five helpers that guard a closed set are copy-pasted: `NonBlank`, the `_Strict` pydantic base, the repo-relative path validator, the spec-major extraction, and the git blob SHA. When this ticket is done, each of these has one definition, and every other site imports or derives from it. Adding a member or fixing a validator then needs one edit, not a hunt across modules (roadmap section 2.2 and 2.3, row 19).

This ticket covers only the sets and helpers named in Scope in. The other section 2.2 rows (settled/retired states, failed-attempt terminals, surfaces, spike kinds, box classes, triage verdicts, control verbs, ask kinds, finding codes, conduct-file routing) are not touched here. `dev.py` currently holds no hard-coded tier, priority or kind choices, so it needs no edit.

## Scope in / Scope out
Scope in:
- Tiers: `llm.AgentTier` is the owner. `config.Tier`, `tickets.Level`, `caps.LEVELS` and `policy.TIERS` derive from it (alias or `get_args`) and keep their current values and order `low, medium, high, max`.
- Priorities and kinds: `tickets.py` owns `Priority` and `Kind` aliases plus `PRIORITIES` and `KINDS` tuples, used by `Frontmatter` and `template`. The canonical order is `PRIORITIES = ("P0", "P1", "P2", "P3")` and `KINDS = ("feature", "bug", "chore")`, the order the CLI and `tickets.template` use today. `Frontmatter.kind` takes the `Kind` alias, so its Literal order changes from `bug, feature, chore` to the canonical order; the set members do not change. In `__main__.py`, the `new --kind` choices and the ordering `--priority` choices derive from `KINDS` and `PRIORITIES`. The `author.py` skeleton kind list (`feature, chore, bug`) derives from `tickets.KINDS`, so it takes the canonical order. The CORE_TEMPLATE text in `hostfiles.py` names the verb, not the list: edit it only if it holds a hand-copied list, and only if no pinned byte budget changes.
- `NonBlank`: one definition in `artifacts.py`. `author.py`, `triage.py`, `box.py` and `inbox.py` import it. Values that are whitespace-only are still refused; the one behavior change is that artifacts' stripping applies to these sites too.
- `_Strict`: one base in `artifacts.py` (`ConfigDict(strict=True, extra="forbid", frozen=True)`). `stages.py` drops its identical `_Strict` and uses `artifacts._Strict`. `box._Strict`, `inbox.Strict` and `config._Strict` are named exceptions: they are not frozen, so they keep their own classes. The run record names this.
- Path validator: one `repo_relative_path(value: str) -> str` in `artifacts.py` that raises `ValueError`. It refuses blank, absolute, `..` and `.` segment, backslash and NUL values. It does not refuse a trailing slash, because `tickets._repo_path` validates Scope fence prefixes such as `clutch/`. `box.py`, `inbox.py`, `config.py` and `covgate.py` call it, and `tickets._repo_path` wraps it into a Finding. `covgate.paths` keeps its normal-form check `str(PurePosixPath(path)) != path` as a covgate-only rule on top of the shared call, so `covgate` still refuses `"a/"` and `"a//b"`; that check is not a second validator.
- Spec major: one `spec_major(version: str) -> int` in `artifacts.py`. It replaces the `int(version.split(".")[0])` sites in `requisition.py`, `rework.py`, `policy.py`, `baseline.py` and `artifacts.py`, and the uncalled `stages._major` is deleted.
- Blob SHA: one `git.blob_sha(data: bytes) -> str` in `git.py`. It replaces the hand-rolled hash in `requisition.py`, `hostfiles.py` and `stages.py`.

Scope out: behavior changes beyond those listed, the other section 2.2 rows, the retro-recurrence boundary, signal-body builders, `main-verb-groups` items, and docs edits. Existing tests that pin values stay unchanged. If an existing test must change, stop and name it in the run record.

## Scope fence
- clutch/artifacts.py
- clutch/author.py
- clutch/triage.py
- clutch/box.py
- clutch/inbox.py
- clutch/config.py
- clutch/stages.py
- clutch/requisition.py
- clutch/rework.py
- clutch/policy.py
- clutch/baseline.py
- clutch/hostfiles.py
- clutch/covgate.py
- clutch/tickets.py
- clutch/llm.py
- clutch/caps.py
- clutch/git.py
- clutch/__main__.py
- tests/unit/test_closed_sets_single_helpers.py

## Acceptance criteria
1. `tests/unit/test_closed_sets_single_helpers.py::test_helpers_have_one_definition` asserts `author.NonBlank`, `triage.NonBlank`, `box.NonBlank` and `inbox.NonBlank` are each `artifacts.NonBlank` by identity, not separate equal copies. It also asserts `stages._Strict is artifacts._Strict`, not a separate class with the same config.
2. `tests/unit/test_closed_sets_single_helpers.py::test_repo_relative_path` asserts `artifacts.repo_relative_path` returns `"a/b.py"` unchanged and raises `ValueError` for `""`, `"/abs"`, `"../x"`, `"a/../x"`, `"./x"`, `"a\\b"` and a NUL-containing value. Returning the input for any of those fails the test. It also asserts `repo_relative_path("clutch/")` returns `"clutch/"`, not raises.
3. `tests/unit/test_closed_sets_single_helpers.py::test_spec_major_and_blob_sha` asserts `artifacts.spec_major("3.4") == 3`, not `"3"` and not `3.4`. It also asserts `git.blob_sha(b"hello\n")` equals `"ce013625030ba8dba906f756967f9e9ca394464a"`, the value `git hash-object` gives for that content, and that `stages` has no `_major` attribute.
4. `tests/unit/test_closed_sets_single_helpers.py::test_vocabularies_derive_from_one_owner` asserts `tickets.PRIORITIES == ("P0", "P1", "P2", "P3")`, `tickets.KINDS == ("feature", "bug", "chore")`, and `caps.LEVELS == policy.TIERS == get_args(llm.AgentTier) == ("low", "medium", "high", "max")`. It also asserts `get_args(tickets.Kind) == tickets.KINDS`, so the `Frontmatter` kind Literal is not a separate copy.
5. `tests/unit/test_closed_sets_single_helpers.py::test_argparse_choices_derive` builds the CLI parser from `clutch.__main__` and asserts the `new --kind` and ordering `--priority` choices equal `tickets.KINDS` and `tickets.PRIORITIES` as tuples.
6. `tests/unit/test_closed_sets_single_helpers.py::test_covgate_keeps_normal_form_check` asserts `covgate` still refuses the `[coverage.files]` key `"a/"`, and does not accept it because the shared validator allows a trailing slash.
7. The existing pins still pass unchanged: `./dev.py test tests/integration/test_closed_sets.py`.
8. `./dev.py test tests/unit` exits 0 with no edit to any existing test file.

## Verification
```
./dev.py test tests/unit/test_closed_sets_single_helpers.py
./dev.py test tests/integration/test_closed_sets.py tests/integration/test_cli.py tests/integration/test_hostfiles.py tests/integration/test_config.py tests/integration/test_box.py tests/integration/test_inbox.py
./dev.py test tests/unit
```

## Definition of rejected
A branch that leaves a second `NonBlank`, a second `stages` strict base, a second path validator (the covgate-only normal-form check is not one), a spec-major expression or a hand-rolled blob hash in the listed modules. A branch that adds a compat alias or dual path instead of updating every call site, edits an existing test's expected values to pass, or changes the members of the kind set, or the order or members of the tier or priority sets. A branch that makes `box._Strict`, `inbox.Strict` or `config._Strict` share the frozen base.

## Time budget
- expected: 90m
- stuck: 120m
