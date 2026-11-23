---
state: confirmed
source: human
priority: P2
kind: chore
---

## Depends on
- none

## Context
- clutch/hostfiles.py::CORE_TEMPLATE
- tests/integration/test_hostfiles.py::test_core_template_order_and_budget
- tests/integration/test_hostfiles.py::test_core_template_is_host_neutral
- tests/integration/test_core_supervisor_verdicts.py

## Goal / Why
The first HARD rule in `CORE_TEMPLATE` (`clutch/hostfiles.py`) sends every requested chat change to repo content, docs included, through a drafted ticket unless the owner types an explicit override. For a new document, or a documentation-only edit that records a plan, design, or decision reached in the chat, that loses context: the implementing agent sees only the ticket and its Context files, not the chat, so the reasoning is summarized away or rebuilt by guesswork. On 2026-11-22 the owner hit this writing `docs/provider-roles-plan.md`: the drafted ticket carried the facts but none of the design reasoning, and the doc had to be written on main by override. Existing plans (`docs/stage-panels-plan.md`, `docs/training-data-plan.md`) were already written directly as `docs:` commits.

When done, the rule carries a new exception: in interactive chat, a new document or a documentation-only edit with no matching code change that records a plan, design or decision from the chat may be written on main without an override, to keep the chat's reasoning. The exception does not cover agent rule files (CLAUDE.md, AGENTS.md, the core template), generated files, or frozen documents; those stay ticketed. Committing still needs the owner to say commit.

Home: this rule governs chat sessions in every host, so it belongs in `CORE_TEMPLATE` and reaches this repo's `CLAUDE.md` and `AGENTS.md` through the managed block, never written only into this repo's files.

## Boundary contract
### Core conduct template
- disposition: extend
- owner: clutch/hostfiles.py
- consumers: `clutch host core` rendering into each host's routed conduct files; this repo's CLAUDE.md, AGENTS.md and the fixture host's CLAUDE.md
- observable change: the first HARD rule of `## Ticket authoring` lists a sixth exception allowing chat-originated new docs and documentation-only edits on main
- compatibility: every other rule keeps its meaning; phrases pinned by `test_core_template_is_host_neutral` stay verbatim; the template stays at most 8192 bytes
- acceptance: the new test finds the exception text and its exclusions in `CORE_TEMPLATE`; the managed blocks match the template byte for byte
- tests: tests/unit/test_hostfiles_docs_on_main.py, tests/integration/test_hostfiles.py, tests/integration/test_core_supervisor_verdicts.py
- post-merge source of truth: clutch/hostfiles.py

## Scope in / Scope out
Scope in:
- In `CORE_TEMPLATE`, add exception (6) to the first HARD rule of `## Ticket authoring`, worded to this effect: "(6) a new document, or a documentation-only edit with no matching code change, that records a plan, design, or decision from this chat; never agent rule files (CLAUDE.md, AGENTS.md, the core template), generated files, or frozen documents". Extend the rule's `Why:` with one clause saying ticketing such docs loses the chat's reasoning.
- The template is at 8191 of its 8192-byte budget. Free the bytes the new text needs by tightening wording elsewhere in `CORE_TEMPLATE` without dropping or weakening any rule, and keep every phrase `test_core_template_is_host_neutral` asserts verbatim. The template must stay host neutral (none of the terms that test forbids).
- Refresh the managed block in `CLAUDE.md` and `AGENTS.md` with `uv run clutch host core`, and copy the same block into `hosts/fixture/CLAUDE.md` so all three match the template byte for byte.
- Add `tests/unit/test_hostfiles_docs_on_main.py` (imports `CORE_TEMPLATE` only, no disk): asserts `CORE_TEMPLATE` contains the exception's distinguishing phrase (for example "documentation-only edit") and names `CLAUDE.md`, `AGENTS.md` and generated files as excluded within that same rule paragraph.
Scope out: no change to project-owned rules outside the managed blocks, to shipped host guides, or to any code path; no change to the supervising-fixes exception.

## Scope fence
- clutch/hostfiles.py
- CLAUDE.md
- AGENTS.md
- hosts/fixture/CLAUDE.md
- tests/unit/test_hostfiles_docs_on_main.py

## Acceptance criteria
1. `./dev.py test tests/unit/test_hostfiles_docs_on_main.py` passes, and fails if exception (6) is removed or its exclusion of agent rule files is dropped.
2. `./dev.py test tests/integration/test_hostfiles.py` passes: the template stays at most 8192 bytes, host neutral, and keeps every pinned phrase.
3. `./dev.py test tests/integration/test_core_supervisor_verdicts.py` passes: `CLAUDE.md`, `AGENTS.md` and `hosts/fixture/CLAUDE.md` managed blocks equal `CORE_TEMPLATE`, not the pre-change text.

## Verification
```
./dev.py test tests/unit/test_hostfiles_docs_on_main.py tests/integration/test_hostfiles.py tests/integration/test_core_supervisor_verdicts.py
```

## Definition of rejected
The compression drops or weakens any existing rule, the exception admits agent rule files or code changes, or any file outside the fence changes.

## Time budget
- expected: 20m
- stuck: 40m
- reason: compressing an 8 KB template to fit new text needs careful rewording, not splittable from the rule it makes room for
