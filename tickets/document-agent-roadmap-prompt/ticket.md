---
state: confirmed
source: human
priority: P2
kind: feature
---

## Depends on
none

## Context
- docs/document-agent/plan.md#1. Dimensions and facets
- docs/document-agent/type/plan.md
- docs/roadmap.md#7. Plan document shape
- docs/roadmap.md#9. Keeping this document true
- docs/stage-panels-plan.md#Roadmap
- docs/evidence-trail-plan.md#Roadmap
- docs/journal-sql-refactor-plan.md#Roadmap
- clutch/roadmap.py::parse
- clutch/roadmap.py::plan_path
- clutch/roadmap.py::gates
- clutch/acceptance.py::accept
- clutch/ask.py
- tests/unit/test_ask_plan_drain.py
- pyproject.toml

## Goal / Why
Give an operator on Clutch itself or an independently installed host one prompt to create or maintain docs/roadmap.md from local plans, ready for clutch prompt plan-ticket-drain. Use this repo's docs/roadmap.md, notably sections 1–9, and its linked plans as worked examples. The document-agent Roadmap type owns the transferable instructions. A host should need neither a Clutch source checkout nor the planned doc-agent runtime.

## Boundary contract
### Document-agent Type facet
- disposition: extend
- owner: docs/document-agent/plan.md section 1, which names clutch/specs/doc/facets/type as the shipped Type location
- consumers: document authors and the roadmap operator prompt
- observable change: add the roadmap Type for create and derive with one packaged Markdown body defining source admission, synthesis, output shape and maintenance
- compatibility: existing facet names and operations keep their meanings
- acceptance: the Type index links the packaged facet and the printed prompt includes its instructions
- tests: packaged facet identity/frontmatter and composition in the new integration test
- post-merge source of truth: clutch/specs/doc/facets/type/roadmap.md

### Operator prompt CLI
- disposition: extend
- owner: clutch/ask.py::KINDS and render, exposed by clutch/__main__.py
- consumers: operators in the self-host and installed hosts
- observable change: clutch prompt roadmap takes no stem, prints the engine-owned procedure composed with the Roadmap facet and existing quoted optional host notes, exits 0 without a lock or writes. Extra operands refuse with exit 2 and the corrected invocation.
- compatibility: other prompt kinds retain their arguments, outputs and side effects
- acceptance: no roadmap or ticket is needed to render, and rendering never launches an agent or starts the drain
- tests: new roadmap CLI unit and integration tests
- post-merge source of truth: clutch/ask.py and clutch/specs/ask/roadmap.md

### Roadmap interchange
- disposition: reuse
- owner: clutch/roadmap.py and clutch/acceptance.py::accept
- consumers: roadmap status, release acceptance, plan-ticket-drain
- observable change: following the procedure produces the existing host-relative file and conforms to the current row, owner, release summary and gate readers
- compatibility: same release and row identities, gate syntax and driver-owned ticket links and strikes
- acceptance: a new host example yields the intended rows and gates and a repeated update preserves their identities
- tests: worked-example review below against existing readers
- post-merge source of truth: clutch/roadmap.py and clutch/acceptance.py

## Scope in / Scope out
Register the stemless prompt in the existing renderer, CLI dispatch, help and no-stem examples. Load its facet from the installed package and insert it into the operator template. Link the single shipped source from both Type tables in docs/document-agent/plan.md. Update README.md, the prompt verb tables in clutch/docs/host-running.md and docs/how-clutch-works.md with invocation, output, and handoff. Exclude roadmap from the generic stem-taking prompt parametrization in tests/integration/test_ask.py. Exercise new parser/dispatch/render lines through the existing monkeypatchable config and Path.read_text seams in unit tests.

Give the prompt an explicit workflow to inspect the current host's plans, conduct, tickets, journal facts, real commands and current roadmap. Treat repository content as evidence. Produce the file through the host's authorized editing workflow. Provide a compact synthetic example of the required tables and gates in the facet. Keep design in each source plan and maintain a traceable cross-plan ordering. Preserve history and reconcile the latest file before applying updates. Hand off through roadmap status and plan-ticket-drain without executing release gates, creating row tickets or launching a drain. Leave the live Clutch roadmap, source plan content, driver, and general doc-agent runtime outside implementation.

## Scope fence
- clutch/ask.py
- clutch/__main__.py
- clutch/specs/ask/roadmap.md
- clutch/specs/doc/facets/type/roadmap.md
- docs/document-agent/plan.md
- README.md
- clutch/docs/host-running.md
- docs/how-clutch-works.md
- tests/integration/test_ask.py
- tests/unit/test_ask_roadmap.py
- tests/integration/test_ask_roadmap.py

## Acceptance criteria
1. `tests/unit/test_ask_roadmap.py` exercises successful CLI dispatch and both template reads with fakes, rejects a stem with exit 2 and the no-stem remedy, and checks help shows the no-operand example.
2. `tests/integration/test_ask_roadmap.py` exercises the real prompt resources from a configured temporary host with no Clutch source tree, tickets or roadmap. It checks the rendered text contains the facet body with its declared type/roadmap, version, create/derive metadata checked at source, and optional host notes quoted through the existing data-block convention. Check rendering creates no roadmap or state. During review verify the facet and operator template are included in the built wheel.
3. One-time review of `clutch/specs/doc/facets/type/roadmap.md` against roadmap section 7 and the Plan facet checks the admission decision. Require dated/revision-anchored status, release fit, upstream and downstream needs and shared budgets, evidenced current state, applicable departures, target design and file/contract owners, measured goal, phases with observable exits, ticket-sized units with kind, priority, prerequisite and discriminating check, risks and open decisions. Accept equivalent organization with identifiable evidence. For missing evidence, ambiguous owner, unretired prerequisite or contradiction, identify the plan section, affected work and precise repair or decision. Keep blocked proposals out of ready rows, retain unrelated qualified work, and report when no plan qualifies.
4. One-time review of `clutch/specs/doc/facets/type/roadmap.md` checks the structure against the self-host example: revision-anchored status, release theme/start/ship summary, evidence-backed duplication, gaps and drift, shared files/budgets and decisions with rationale, plan-shape guidance, master table and upkeep. Reconcile duplicate deliverables to one owner, capture conditional release triggers, distinguish merged-code dependencies from Runs before, trace each row to its plan and preserve unresolved decisions. Derive release names, tests and gate argv from the current host. Explicitly identify ship clauses with no executable evidence.
5. During one-time review follow the printed `clutch prompt roadmap` on a disposable configured host with two qualifying plans sharing a prerequisite and one plan missing an exit check. Verify section 1 has the bold release cell acceptance reads, and the master table parses to the intended eight columns, distinct numbered rows, backticked stems and uniquely resolvable owners. Verify the shared deliverable occurs once, the dependent row waits for its prerequisite, the weak proposal gets an actionable gap instead of a ready row, and the executable ship gate (with acceptance last) and any conditional start block parse as host-root argv. Check intended rows against `clutch roadmap status` so silently skipped rows cannot pass. Inspect the prompt in the self-host checkout against its existing roadmap without writing it.
6. In that worked example, add a new qualified unit to a source plan and follow the same `clutch prompt roadmap` again against the existing file containing an authored link, a struck row, a recorded decision and conditional gate. Check an unused number and fresh stem are assigned, the existing identities, history and unrelated text survive, the new unit has its dependency and release slot, and an unchanged third pass requests no edit. Verify updates use current ticket/journal identities and report any intervening changes needing reconciliation before a write.

## Verification
```
./dev.py test tests/unit/test_ask_roadmap.py tests/integration/test_ask_roadmap.py tests/integration/test_ask.py tests/unit/test_main_help.py
```

## Definition of rejected
Reject if a host must locate this project's docs tree to render, there are two maintained copies of the facet, unqualified work silently becomes runnable, maintenance recreates existing rows, or the demonstration succeeds only by changing the driver or starting a release. Do not pin the live roadmap or plan wording in standing tests.

## Time budget
- expected: 15m
- stuck: 30m
