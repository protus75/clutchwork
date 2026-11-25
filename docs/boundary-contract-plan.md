<!-- clutch:meta
schema: clutch.meta/1.0
kind: plan
purpose: Boundary contracts and interface reuse: plan
relates: [clutch/daemon.py, clutch/effects.py, clutch/gates.py, clutch/journal.py, clutch/llm.py, clutch/seams.py, docs/roadmap.md]
owner: engine
verified: 5fee4e67
hash: e68f36e7cbd2751a7c5c6bd9b44d9f93a76ee02863e2ef8a55f75f30a392f4da
-->
# Boundary contracts and interface reuse: plan

Require a ticket to specify the producer/consumer boundaries its change reuses, changes, replaces,
or creates before implementation begins. The requirement is contract-first design, not a mandate to
add a language-level interface or abstraction to every change. Its purpose is to make tickets more
buildable, keep API decisions out of Implement, lead agents to canonical reusable code, and expose a
parallel implementation before it lands.

The owner decisions in this plan fix the section name, required content, exceptions, and staged
enforcement policy. The retrospective trial chose the exact closed Markdown grammar from those decisions; see
[Trial results](#trial-results). The cost of a vague grammar is boilerplate, while the cost of an
over-specific one is speculative abstraction throughout every host repository.

## Status

Merged roadmap rows: 150 (`boundary-contract-trial`), 151 (`boundary-contract-authoring`), 153 (`boundary-contract-implementation-review`), 154 (`boundary-contract-required`), 163 (`docs-truth-after-040`), 208 (`boundary-contract-outcome-compare`). Open roadmap rows: 152. Proposed on 2026-11-18 from an owner design discussion.

## Roadmap

The [master roadmap](roadmap.md#8-master-ticket-table) places the trial and authoring rollout in 0.4.0 (rows 150–151), ahead of the graphics ticket kind. Deployed reviews provide the evidence for stronger lint in 0.5.0 (provisional row 152). Implement and diff review adopt the declared contracts in 0.5.0 (row 153), independently of whether that lint is earned. Roadmap §5 decisions 18–19 cover the shared prompt, managed-block budget and overlap with existing alignment work.

## Problem

The current ticket process checks much of the necessary evidence indirectly:

- `clutch/specs/requisition_review.md` judges whether a ticket is buildable, catches contradictory
  signatures and criteria, traces callers and importers, checks sibling interface changes, accounts
  for dependent tests, and snags missing evidence.
- `clutch/docs/host-authoring.md` requires measurable criteria, complete scope fences, caller and
  importer closure, and tests that rule out a wrong result.
- Implement treats the ticket as the contract and can return `premise_failed` when its requirements
  cannot be satisfied.
- Review checks the resulting diff against acceptance, scope, security boundaries, and consumers
  outside the fence.

None of these surfaces requires the author to state the boundary itself. An agent can therefore
make API decisions during implementation, miss an existing canonical seam, build a second parser or
registry, or create a wrapper that performs behavior already owned elsewhere. Requisition review may
infer the problem, but the decision remains informal and difficult to lint.

The new rule should solve four related failures:

1. **Missing contract:** inputs, outputs, failures, side effects, or compatibility behavior are left
   for Implement to invent.
2. **Missed reuse:** the ticket does not point Implement at the existing owner, representative
   consumer, construction path, and fake.
3. **Parallel ownership:** a new registry, parser, codec, persistence path, factory, or wrapper
   competes with an existing owner.
4. **Unearned abstraction:** a broad interface is introduced for one private call site without an
   external-effect seam, plugin boundary, or evidenced duplicate behavior to justify it.

## Design principles

### Contract-first, not interface-everywhere

“Interface” is ambiguous. It can mean a Python `Protocol`, an exported function, an HTTP endpoint,
a command, a stored record, or any producer/consumer boundary. Requiring literal interface classes
would conflict with this repository's smallest-change, no-speculative-abstraction, no-single-caller-
helper, and no-dual-path rules.

The portable requirement is instead:

> Before implementation, a ticket identifies the existing boundary it reuses or changes, or
> justifies creating a new boundary. Implementation may not invent undeclared APIs or parallel
> ownership paths.

A private helper with one caller in the same unit remains implementation detail. A private symbol
used across independently changeable units is still a boundary even when it is not publicly exported.

### Reuse is the default disposition

A ticket starts from the repository's canonical capability owner. It may create a new boundary only
after naming the closest existing candidates and the concrete incompatibility that prevents reuse.
This is stronger than telling Implement to search: the author and requisition reviewer make the reuse
decision while the ticket can still be repaired cheaply.

### The ticket is temporary; the owner is durable

The ticket is the implementation contract for one change. After merge, the durable truth lives with
the code, schema, command help, or maintained behavior documentation that owns the boundary. The new
section must name that canonical owner; it must not create a second permanent API catalog by accident.

### Observable behavior, not private construction

The contract specifies what consumers can rely on: inputs, outputs, failures, side effects,
invariants, compatibility, and ownership. It prescribes a class hierarchy, algorithm, or internal
decomposition only when that structure is itself a required seam or acceptance condition.

### One production implementation can still earn a seam

Do not require two production implementations. An external-effect boundary commonly has one real
implementation and test fakes, and that is sufficient. Requiring two real implementations would
either forbid useful seams or manufacture dead code.

## What counts as a boundary

The shared definition should be language-neutral and include:

- exported and internal functions, methods, constructors, protocols, callbacks, and object shapes
  consumed outside their owning unit;
- CLI commands, arguments, output, diagnostics, exit codes, and help;
- HTTP, RPC, plugin, provider, and child-process boundaries;
- configuration keys, environment variables, feature switches, and closed vocabularies;
- persisted files, database records, journal events, JSON/YAML documents, snapshots, fixtures, and
  generated artifacts;
- registries, codecs, parsers, factories, hooks, queues, and event schemas;
- user-visible workflows whose state or actions are consumed by an operator, extension, automation,
  or documented integration.

The definition excludes a private implementation detail with no independently changeable consumer.
Moving a calculation into a one-caller helper does not earn an interface contract of its own.

## Proposed ticket content

Every ticket carries a `## Boundary contract` section. “Boundary” covers commands, data, processes,
and user workflows without implying a language feature; the owner chose that name in design decision
1.

Each entry uses one closed disposition:

- `reuse`: consume an existing boundary without changing its contract;
- `extend`: add behavior to an existing boundary;
- `replace`: remove one boundary and move its consumers to another;
- `create`: introduce a new boundary;
- `none`: make no boundary change, with a constrained reason.

### Reuse example

```md
## Boundary contract

### `clutch.seams::ProcessExec`
- disposition: reuse
- owner: `clutch/seams.py::ProcessExec`
- consumers:
  - `clutch/new_module.py::Thing`
- contract change: none
- composition: existing production `SubprocessExec`; injected fake in unit tests
- acceptance: criterion 2
- tests: `tests/unit/test_thing_process_seam.py`
```

### Create example

```md
## Boundary contract

### `clutch.foo::FooStore`
- disposition: create
- owner: `clutch/foo.py::FooStore`
- searched:
  - `clutch/seams.py`
  - `clutch/artifacts.py`
  - `clutch/effects.py`
- reuse rejected:
  - `FileSystem` owns path and byte operations, not Foo record validation or publication
- consumers:
  - `clutch/producer.py::produce`
  - `clutch/consumer.py::consume`
- inputs: ...
- outputs: ...
- failures: ...
- side effects: ...
- invariants: ...
- compatibility: new boundary; no legacy path
- composition: ...
- acceptance: criteria 1 and 3
- tests: `tests/unit/test_foo_store_contract.py`
- canonical owner: `clutch/foo.py`
```

### No-change example

```md
## Boundary contract

none
- reason: private implementation only; existing callers, return values, failures, side effects,
  construction, and persisted formats remain unchanged
```

The exact Markdown syntax should be chosen only after applying it to representative tickets. The
eventual grammar needs to be closed enough for lint without turning the ticket into an IDL that tries
to model every host language.

## Required contract facts

For each created or changed boundary, the ticket should state:

- **Boundary and owner:** exact symbol, command, endpoint, schema, format, or workflow and its one
  canonical location.
- **Disposition:** reuse, extend, replace, create, or none.
- **Consumers:** known callers or readers and whether each changes.
- **Inputs:** names, types or shapes, validation, defaults, and allowed values where observable.
- **Outputs:** type or shape, ordering, persistence, and observable results.
- **Failures:** exceptions, error values, exit codes, diagnostics, retry semantics, and atomicity when
  those are part of the contract.
- **Side effects:** files, processes, network, journal writes, notifications, or state transitions.
- **Invariants:** facts that must survive alternative implementations.
- **Compatibility:** unchanged, intentionally breaking, newly introduced, or removed. A compatibility
  path exists only when the ticket explicitly requires it.
- **Composition:** where the production implementation is selected and wired.
- **Verification:** acceptance criteria and tests that distinguish the contract from a plausible wrong
  implementation.
- **Canonical post-merge owner:** where future authors find the durable contract.

For `create`, also require:

- the existing owners and symbols searched;
- the nearest reuse candidates;
- a concrete incompatibility for each rejected candidate;
- the incident that earns the abstraction.

## Earning a new code-level interface

A new interface should have at least one of these reasons:

1. Two named production consumers need the same boundary.
2. One production consumer needs an injectable fake at an external-effect seam.
3. A plugin, provider, or integration boundary has a named extension requirement.
4. The repository already contains evidenced duplicate behavior in at least two locations and the
   ticket moves those consumers to one owner.
5. A protocol or format crosses a process, storage, package, or independently deployed boundary.

Without one of those reasons, the ticket keeps the behavior concrete and private. These conditions
are candidates for the shared rule, not yet final policy; trials may show that some hosts need a
broader or narrower portable definition.

## Exceptions and preservation claims

The following changes may use `none`, with a reason:

- documentation-only corrections that describe no changed behavior;
- comments, spelling, formatting, and metadata-only changes;
- test-only changes that encode an already-owned contract without changing production behavior;
- regeneration where both the generator and generated contract remain unchanged;
- dependency or version updates proven not to alter a consumed boundary;
- pure private implementation changes whose callers, outputs, failures, side effects, construction,
  and data formats remain unchanged;
- deletion of unreachable private code with no consumers.

These are not exceptions:

- a bug fix: it states whether it restores an existing contract or changes one;
- a refactor: it makes an explicit preservation claim;
- an internal API with independently changeable consumers;
- a fixture or test helper consumed outside its owning test;
- configuration, serialized data, journal records, snapshots, or generated formats;
- a UI behavior consumed by automation, accessibility tooling, an extension, or a documented
  operator workflow;
- a rename observed by any caller, importer, test, document, or persisted value.

`none` is therefore a reviewable preservation claim, not a bypass. Requisition review traces the
consumer closure and snags the ticket when the claim is false.

## Rules that make the contract effective

The section alone would become decorative unless accompanied by these rules:

- **One owner:** every capability has one definition owner and, where applicable, one registry and
  one composition owner.
- **Consumer closure:** account for every affected caller, importer, reader, test, and document; fence
  every one the change forces.
- **Contract-to-criterion traceability:** every new or changed observable behavior maps to an
  acceptance criterion and test obligation.
- **Wrong-implementation test:** each named test fails for a plausible violation, not merely because
  the interface was not executed.
- **Preservation coverage:** properties declared unchanged but put at risk by the change receive a
  test obligation.
- **No accidental expansion:** implementation adds no parameter, output variant, error mode,
  extension point, compatibility path, or side effect absent from the ticket.
- **Explicit breakage:** a breaking contract identifies all migrations in the same ticket or in
  dependency-ordered tickets; no defensive dual path is inferred.
- **Sibling consistency:** a sibling that consumes a proposed contract cites the same owner and
  contract or depends on the ticket that establishes it.
- **No implementation-time policy:** a material omitted contract choice produces `premise_failed`;
  Implement does not invent it.
- **Smallest interface:** expose only the behavior required by named consumers.

## Organizing a host for discovery and reuse

The rule will reduce duplication only when an agent can find the canonical owner efficiently. Hosts
should optimize for a short path from “I need capability X” to its owner rather than merely creating
more directories or abstract base classes.

### Capability ownership

Use modules named for the capability they own, not generic buckets such as `utils`, `helpers`,
`common`, `services`, or a global `interfaces` dumping ground. Clutch already has useful examples:

- `clutch/seams.py`: cross-cutting external effects and their injectable contracts;
- `clutch/llm.py::LLM`: the model boundary;
- `clutch/gates.py::Gate`: gate behavior;
- `clutch/git.py`: the sole Git operation path;
- `clutch/providers.py`: provider implementations and registry;
- `clutch/tickets.py`: ticket grammar;
- `clutch/specs/__init__.py`: prompt loading and validation.

Domain interfaces normally live beside their canonical implementation. A global seam module is
appropriate only for a narrow category such as external effects.

### Searchable owner language

Canonical modules should open with short factual ownership docstrings using consistent terms such as
`owner`, `contract`, `seam`, `adapter`, `registry`, `projection`, `codec`, and `store`:

```python
"""Foo record contract and its sole persistence owner.

Use FooStore for reading and publishing Foo records. Do not read the backing JSON directly.
"""
```

These are not broad architecture essays. They make repository search and adjacent-code reading lead
an agent to the paved road.

### Closed registries and centralized composition

Extensible implementation sets use one canonical closed registry. Callers do not introduce parallel
conditionals or lookup tables. A ticket that adds an implementation names the interface, registry,
existing implementations inspected, exact-equality tests, and documentation it affects.

Production implementations are selected in one composition owner. Consumers receive the selected
implementation through the established constructor or function boundary. This makes four roles
discoverable:

- interface owner defines the contract;
- implementation owner performs the capability;
- composition owner selects and wires it;
- consumer depends only on the contract.

### Context carries the paved road

A `reuse` ticket should include in `## Context`:

- the exact interface definition;
- its canonical implementation or factory;
- one representative existing consumer;
- one representative test using its fake or supported construction path.

A `create` ticket includes the closest rejected alternatives. Requisition review should snag a reuse
disposition whose owner and representative usage are absent from Context. This is more effective than
an instruction to search because the relevant artifacts enter Implement's prompt directly.

### Tests teach supported use

Focused tests should demonstrate the normal fake and construction path. A host undermines reuse when
nearby tests monkeypatch raw effects in several incompatible ways. Clutch's `testguard`, which blocks
raw process and network use in unit tests, is an existing example of making the supported seam the
easiest path.

## Optional generated discovery view

A compact interface catalog could help authors and Implement find owners:

```text
ProcessExec
  owner: clutch/seams.py::ProcessExec
  production: clutch/seams.py::SubprocessExec
  consumers: clutch/git.py, clutch/providers.py, ...
  category: process effect
```

It must be generated from code-owned declarations or another checked single source. A handwritten
catalog would become a competing authority and violate the ownership rule this plan is trying to
establish. Do not build the catalog in the first rollout. First observe whether Context requirements,
owner docstrings, and repository search leave a recurring discovery failure.

## Engine plane and host plane

ClutchWork should share and enforce ticket-level contract discipline across hosts, but it must not
impose one code architecture.

| ClutchWork owns | Host repository owns |
|---|---|
| Required contract section and closed dispositions | What concrete boundaries exist in the host |
| Reuse-first authoring and review workflow | Canonical locations, naming, and dependency directions |
| Resolvable owner, consumer, Context, criterion, and test references | Language- and framework-specific API rules |
| Review of unjustified creation and undeclared boundaries | Generated-code, migration, and framework exceptions |
| Diff conformity to the ticket contract | Stronger static architecture checks |
| Generic `none` preservation claim | Evidence that a particular change qualifies for `none` |

Portable policy must not require Python `Protocol`, dependency injection, repository classes,
OpenAPI, or any other particular implementation device. A host may require those in its own
architectural conduct. The engine reads that project content but does not hard-code it.

Do not add an `interface_policy: strict|relaxed|python` configuration matrix. That would create
multiple authoring processes. One broad boundary model, a constrained `none`, and host-owned stronger
rules provide variation without multiplying ticket formats.

## Where the eventual rules belong

| Concern | Owner |
|---|---|
| Portable behavioral requirement to declare and reuse boundaries | `CORE_TEMPLATE` in `clutch/hostfiles.py` |
| Full ticket content and exception rules | `clutch/docs/host-authoring.md` |
| Section name, skeleton, grammar, and mechanical lint | `clutch/tickets.py` |
| Buildability, reuse, consumer closure, and `none` judgment | `clutch/specs/requisition_review.md` |
| No invention of omitted contract decisions | `clutch/specs/implement.md` |
| Diff conforms; no undeclared parallel owner | `clutch/specs/review.md` |
| Current behavior | `docs/how-clutch-works.md` |
| Clutch-repository-specific architecture constraints | `CLAUDE.md` and `AGENTS.md`, outside the managed block |

The final division between `CORE_TEMPLATE` and the host-authoring guide needs care. The core should
carry the short behavioral obligation; detailed ticket content belongs only in the one authoring
source. It must not restate the grammar or create a second authoring guide.

## Enforcement ladder

### 1. Mechanical ticket lint

High-confidence checks:

- the section exists and has one valid disposition per entry, or the constrained `none` form;
- `reuse`, `extend`, and `replace` name an existing resolvable owner;
- the owner is present in Context;
- `create` has searched candidates, reuse-rejection reasons, consumers, an owner, criteria, and tests;
- named paths and statically resolvable symbols exist unless Scope in says the ticket creates them;
- contract entries cite acceptance criteria and tests;
- changed consumers and registries are fenced;
- a registry implementation names the canonical registry.

Lint can prove shape and referential consistency. It cannot prove that prose completely specifies an
API or that no semantically equivalent implementation exists elsewhere.

### 2. Requisition review

The model judges whether:

- the declared owner really provides the needed behavior;
- an existing owner was overlooked;
- a new abstraction meets an earning condition;
- inputs, outputs, failures, side effects, and invariants are complete enough to implement;
- consumers and composition are fully accounted for;
- `none` is credible against the reference closure;
- siblings agree on a proposed contract;
- criteria and tests distinguish plausible wrong implementations.

Insufficient evidence is a repairable `snag`, not permission for Implement to decide.

### 3. Check and diff review

The resulting diff is checked for:

- conformance between declared and actual signatures or schemas;
- use of the declared owner and composition path;
- no undeclared exported boundary;
- no raw external effect around an existing seam;
- no second registry, parser, codec, factory, persistence path, or compatibility path;
- no consumer break outside the fence;
- no test that passes while the real path violates the contract.

Language-specific AST or schema checks may later cover stable high-value surfaces such as exported
Python symbols, CLI parser entries, registries, closed vocabularies, schemas, and extension snapshot
fields. Semantic duplication remains primarily a review judgment.

## Current repository assessment

A static architecture review on 2026-11-18 covered the approximately 20,800 lines in
`clutch/*.py`, the evidence package, `dev.py`, and the VS Code extension. The review asked two
different questions that must not be confused:

1. How much current code would benefit from clearer boundary ownership or reuse?
2. Which kinds of code are a poor fit for a detailed boundary contract even when they are well
   implemented?

The repository is already substantially aligned with this plan. It does not need a wholesale
rewrite before the ticket rule can be introduced. A reasonable qualitative estimate is that 65-75%
of the structural foundation already exists: explicit effect seams, single-owner registries and
schemas, reusable test fakes, and several modules with clear ownership statements.

### Existing strengths

- `clutch/seams.py` owns clock, sleep, process, notification, and filesystem effects.
- `clutch/llm.py` owns the LLM request/result contract and its scripted fake.
- `clutch/gates.py` owns the gate protocol and gate report.
- `clutch/providers.py` has one provider adapter registry.
- `clutch/tickets.py` owns ticket grammar and parsing.
- `clutch/evidence/schema.py` owns versioned evidence shapes, while
  `clutch/evidence/store.py` persists them through the filesystem seam.
- `tests/fakes.py` provides shared clock, process, filesystem, journal, and Git fakes.
- The Python package has no top-level import cycle.
- Existing conduct already requires single owners, injectable effects, closed vocabularies, and a
  thin extension.

These are examples the boundary-contract rule should preserve and make easier for authors to find.
The rule should not force these modules to acquire another abstraction layer.

### Concentrated alignment work

#### Orchestration ownership

The most difficult ownership area is the cluster formed by `runner.py`, `daemon.py`, `serve.py`,
`drain.py`, `merge.py`, `mergequeue.py`, `driver.py`, and `stages.py`. There are no top-level import
cycles, but these modules use many function-local imports to reach one another. If local imports are
included in the dependency graph, 49 modules participate in one strongly connected component.

That fact does not make the current code incorrect. It means a ticket author must read several large
modules to answer basic contract questions: who owns dispatch, composition, the running lifecycle,
merge admission, and production wiring? The useful refactor is to make those existing ownership
boundaries explicit, not to introduce a new generic orchestration framework.

Estimated work: 4-7 narrowly scoped tickets. Some may already overlap planned single-owner work and
must not be duplicated.

#### Stage responsibilities

`clutch/stages.py` is about 1,609 lines and exposes about 50 public symbols. It participates in
artifact validation, prompt-stage composition, run-record rendering, outbox lifting, host-command
execution, evidence gathering, Check, Review, and scope-fence matching.

The clearest ownership mismatch is scope-fence matching. `_in_fence` is private to `stages.py`, but
`requisition.py` imports it and `mergequeue.py` reaches it through the `stages` module. Fence
semantics belong with ticket or path policy, not with stage execution.

Estimated work: 3-5 tickets, beginning with the fence/path owner. Further splits should happen only
where responsibilities change independently; file size alone is not a reason to split a module.

#### CLI entrypoint and composition

`clutch/__main__.py` contains a roughly 607-line parser builder, a roughly 568-line command
dispatcher, daemon and serve composition, notification composition, provider construction, and
command-specific behavior. It directly depends on about 25 Clutch modules. Runtime modules also
locally import `__main__`, making the CLI entrypoint part of an internal composition interface.

The parser and command help correctly stay together under the current command-help rule. The useful
refactor is limited to production composition or command behavior that runtime modules currently
reach through the CLI module. Moving parser ownership elsewhere merely to shrink the file would make
the command contract harder to find.

Estimated work: 3-5 tickets.

#### Filesystem ownership

The filesystem seam is well defined, but use is mixed. Modules that already receive a `FileSystem`
still perform some direct `Path.read_text`, `Path.read_bytes`, existence, traversal, or replacement
operations. The largest concentrations found by the static review were `stages.py`, `observe.py`,
`runner.py`, `roadmap.py`, and `__main__.py`.

Not every direct read is a defect. A low-level persistence owner, pure parsing entrypoint, or
operator-only launcher may legitimately use a path directly. Before refactoring, the project must
decide whether the seam owns every filesystem observation or only durable and mutable effects. The
current conduct says filesystem access goes through seams, while the implementation follows a mixed
model.

Estimated work: 4-8 tickets after the ownership decision, grouped by capability rather than as a
repository-wide mechanical rewrite.

#### Test implementations

`tests/fakes.py` is used by about 30 test files, but nine test files still define a local
`FakeExec` or `RecordingExec`, and 17 unit-test files monkeypatch `Path` operations directly. Some
local fakes exercise special behavior and should remain local. Others may be older equivalents of
the shared fake.

Estimated work: 2-4 tickets after classifying the local implementations. Consolidate only
behaviorally equivalent fakes; do not grow one universal test harness.

#### Ownership discovery

Modules such as `seams.py`, `llm.py`, `git.py`, `redact.py`, and the evidence modules already have
clear ownership docstrings. The orchestration modules describe their immediate jobs but do not always
explain their relationship to neighboring composition and lifecycle owners.

Estimated work: 1-3 documentation-focused tickets. Do not build the generated discovery view unless
deployed tickets show that Context, owner docstrings, and repository search are still insufficient.

### Surfaces well suited to full contracts

These surfaces have crisp consumers and observable shapes. A change to them will usually benefit
from a full boundary entry rather than `none`:

| Surface | Current owners |
|---|---|
| Ticket grammar | `clutch/tickets.py` |
| Configuration schema | `clutch/config.py` |
| Stage and review artifacts | `clutch/artifacts.py`, relevant parts of `clutch/stages.py` |
| External effects | `clutch/seams.py` |
| LLM requests and results | `clutch/llm.py` |
| Gate behavior and reports | `clutch/gates.py` |
| Provider adapters | `clutch/providers.py` |
| Git operations | `clutch/git.py` |
| Journal records | `clutch/journal.py` |
| Control messages | `clutch/control.py` |
| Evidence formats | `clutch/evidence/schema.py`, `clutch/evidence/store.py`, evidence adapters |
| Command-line behavior | `clutch/__main__.py` |
| Extension snapshot and commands | `clutch/observe.py`, `vscode-clutchwork/extension.js` |
| Box and decision records | `clutch/box.py` |
| Prompt reply schemas | `clutch/specs/*.md` when their declared output changes |

### Code poorly suited to a detailed mandatory contract

This section describes applicability, not implementation quality. These files and changes may be
well implemented while still being a poor fit for a long API-style contract.

#### Prompt wording without a schema change

Prompt specs often change judgment guidance, examples, or emphasis while keeping the same inputs and
reply schema. A full inputs/outputs/failures contract would restate unchanged facts and hide the
actual wording change. Use a full entry when a prompt's inputs, reply JSON, verdicts, or semantic
promise changes. Use a concise preservation claim for wording-only calibration.

#### Pure private transformations

Private calculations in modules such as `caps.py`, `policy.py`, `baseline.py`, `calibration.py`,
`scorecard.py`, `stats.py`, and `graph.py` are usually implementation details when their existing
module-level output remains unchanged. A ticket should state the preserved output contract, not
describe every intermediate helper or algorithm.

#### Private orchestration helpers

Nested callbacks and local helpers in `serve.py`, `drain.py`, `driver.py`, and `stages.py` are often
specific to one process lifetime. Treating each callback as an interface would make tickets longer
without improving buildability. Only cross-module dispatch, lifecycle, admission, effect, and
composition boundaries need full entries.

#### Extension rendering helpers

DOM and SVG helpers such as `el`, `section`, and `drawCircle` under
`vscode-clutchwork/media/` are private rendering details. Snapshot fields, webview messages, command
identifiers, and VS Code registrations are real boundaries; individual drawing helpers are not.

#### Developer launcher internals

`dev.py` has user-visible commands, so their names, arguments, side effects, and exit behavior are
contracts. Its temporary paths, version extraction, packaging sequence, and internal helper structure
do not each need separate entries.

#### Tests that pin an existing contract

Most local test changes should use a preservation claim. A full entry is useful only when changing a
shared fixture, imported test helper, regression protocol, reusable fake, or fixture/data shape
consumed outside that test.

#### Documentation, metadata, and generated settings

Prose, changelogs, comments, spelling, package metadata, and regenerated settings normally use
`none` when they do not alter a consumed promise. A document is a real boundary when it is itself the
owning specification, such as command help, the host contract, or schema documentation.

#### Migrations and one-time transforms

A migration needs a contract for its source version, destination version, failure behavior, and
idempotence. Its private decomposition is intentionally single-purpose and should not be forced into
a reusable interface.

### Refactor scope estimate

The contract rule and current-code refactor are separate bodies of work:

| Scope | Estimated tickets | Content |
|---|---:|---|
| Policy adoption | 4-6 | Trial, ticket grammar, authoring/requisition review, lint, Implement and Review behavior |
| Minimum high-value code alignment | 8-12 additional | Fence owner, composition boundaries, selected filesystem paths, owner documentation, fake reuse |
| Strong architecture alignment | 15-22 additional | Split ambiguous stage/CLI responsibilities, normalize effect ownership, clarify orchestration composition |
| Exhaustive cleanup | 18-30 additional | Includes lower-value test and private-helper normalization |

The recommended target is policy adoption plus the 8-12 high-value code tickets. Deploy the rule and
let real ticket findings earn deeper refactors. Refactoring the entire package before using the rule
would reverse the useful evidence order.

The target must not be “every changed symbol gets a contract.” A practical target is:

1. Every ticket has a boundary section or a constrained preservation claim.
2. Full entries apply to cross-module, persisted, process, CLI, plugin, schema, configuration, and
   user-visible boundaries.
3. Private calculations and local callbacks stay implementation details.
4. Orchestration tickets name only the lifecycle boundaries they affect.
5. New abstractions justify themselves through consumers, effects, plugins, duplication, or an
   external format.

## Rollout

### Phase 0: retrospective trial

Apply the proposed section by hand to 10-20 representative merged tickets without changing the
engine. Include:

- reuse of an existing external-effect seam;
- creation of a justified seam;
- CLI behavior;
- configuration and a closed vocabulary;
- a persisted or journal format;
- extension snapshot data;
- a private bug fix restoring behavior;
- a refactor preserving boundaries;
- a documentation-only change;
- generated output;
- a sibling-ticket contract dependency.

Record where authors disagree, where the form becomes boilerplate, what facts review actually needs,
and which fields are consistent enough to lint. The phase exits with a chosen section name, closed
dispositions, required fields, earning conditions, and `none` reasons.

### Phase 1: authoring and requisition review

Add the section to the ticket skeleton, authoring guide, Author input, and requisition review. Make
the section structurally mandatory, but initially keep semantic completeness in requisition review.
Do not add a discovery catalog or language-specific gates.

### Phase 2: stable mechanical lint

Add only checks demonstrated by Phase 1 findings: malformed dispositions, missing owners, unresolved
references, absent Context owners, missing criteria/tests, incomplete create justification, and
unfenced named consumers. Keep semantic completeness out of regexes.

### Phase 3: implementation and diff conformity

Teach Implement to stop on omitted material choices and Review to reject undeclared boundaries and
parallel ownership. Measure premise failures, review findings, rework, and duplicate-owner incidents
before and after the change.

### Phase 4: earned specialized checks

Only repeated incidents earn specialized static gates. Decision 9 closes the discovery catalog proposal. Each new check needs a
language-neutral application or a clearly host-owned implementation. Do not grow Clutch into a
partial cross-language type system.

## Trial results

This paper trial read the ticket and run record for each of these 12 merged tickets; it did not
change them. Each line applies the form to the historical change, rather than claiming that the
historical ticket already contained the form. Criteria and tests refer to that ticket's own
acceptance and verification. The owner is also the post-merge source of truth unless stated
otherwise. An unchanged contract is a preservation claim, not a claim that no code changed.

- `fs-seam-mkdir-remove` — reuse of an existing external-effect seam: **extend**
  `clutch/seams.py::FileSystem`; consumers `enginelog`, `journal`, and `stages` replace raw directory
  creation and removal with injected `mkdir` and `remove`. Existing operations stay compatible;
  production and fakes implement the added operations. Acceptance and seam tests cover both. Author
  disagreement: whether to call this reuse or extend; extend records the added methods.
- `dispatch-admission-boundary` — creation of a justified seam: **create**
  `clutch/daemon.py::DaemonAdmission`, consuming injected `clutch.runner.Dispatch`. It serializes
  calls, passes the ticket and terminal through, propagates failure and cancellation, and awaits
  cleanup before releasing the slot. The existing scheduler owns selection and the runner owns
  execution, so neither owns this single-flight task lifetime. The independently consumed async
  callback boundary earns creation; production composition is deferred to `scheduler-activation`.
  Its acceptance and admission tests include cancellation and dormancy. Author disagreement: a
  dormant boundary alone might seem speculative; the named activation is its consumer.
- `cli-group-config` — CLI behavior and sibling-ticket contract dependency: **replace** the three
  top-level config verbs with `config init`, `config update`, and `config migrate`, owned by
  `clutch/__main__.py`; operators, guides and tests migrate together. Arguments, output, writes and
  exits are preserved except for the stated help, refusal and road changes; old names exit 2 with no
  alias. Criteria and group, CLI and guide tests cover migration. It depends on `cli-help-standard`
  for the command-help contract. Author disagreement: whether preserved handler behavior needs a
  claim; it does, because the command names break while handler behavior must survive.
- `closed-dispatch-signal-vocabularies` — configuration or a closed vocabulary: **extend** the
  journal contract owned by `clutch/journal.py` and dispatch producers and consumers in
  `clutch/runner.py` and `clutch/drain.py`. Dispatch becomes a closed exhaustive vocabulary and
  unknown signal names fail at the write seam; valid records remain usable. Its criteria and tests
  cover invalid names and consumers. It depends on `plan-bound-reject-release` for the release
  behavior it classifies. Author disagreement: two related vocabularies need distinct entries in a
  real ticket even though this trial summarizes them together.
- `journal-roll` — persisted or journal format and reuse of an existing external-effect seam:
  **extend** journal append/rotation, owned by `clutch/journal.py`, using the existing filesystem
  publication seam. Readers retain ordered durable history and existing append callers retain their
  contract; rotation occurs at the size or age boundary. Criteria and journal tests cover history
  and rotation. Author disagreement: reuse of the filesystem seam is a separate entry from the
  changed journal boundary.
- `badge-stopped-backlog` — extension snapshot data: **extend** the snapshot badge consumed by the
  extension, owned by `clutch/snapshot.py`. When stopped, it carries blocked plus queued count and
  a stopped tooltip, or `None` at zero; alive behavior is preserved. The extension renders the
  supplied value. Criteria and snapshot tests distinguish stopped and alive cases. Author
  disagreement: whether the rendering consumer needs naming despite no extension edit; it does.
- `consumer-error-keeps-capture` — private bug fix restoring behavior: **extend** the process and
  provider capture contract, owned by `clutch/seams.py` and `clutch/providers.py` respectively.
  A failing stdout consumer must still leave full stdout and stderr in the attempt spool; consumers
  include `CliAdapter.invoke` and later spool readers. Criteria and tests cover the raised callback
  and capture. Compatibility is restoration of the documented capture behavior. Author disagreement:
  `none` would hide an observable failure and persisted output; restoration needs full entries.
- `journal-last-transition-helper` — refactor preserving boundaries: **create** the shared lookups
  `clutch/journal.py::last_transition` and `clutch/effects.py::Effects.recorded`, consumed by the
  previously inline callers. The multiple named consumers and duplicated scans earn consolidation;
  existing latest-transition and recorded-effect results remain unchanged. The closest candidates
  are those inline scans and `Effects._recorded`; they do not provide one shared owner to all
  callers. Criteria and lookup tests cover the results. Author disagreement: a preservation claim
  does not eliminate the new internal boundaries.
- `docs-truth-sweep` — documentation-only change: **none**; reason: documentation corrections
  describe existing behavior; production callers, outputs, failures, side effects and formats remain
  unchanged. The ticket's criteria compare corrected statements to code. Author disagreement: the
  documents are consumed, but their corrected descriptions do not change the described behavior.
- `core-renderer` — generated output: **extend** `clutch/hostfiles.py` core rendering and the
  generated managed conduct blocks consumed by hosts; preserve project bytes outside the routed
  block. The renderer is the source of truth, not the rendered files. Criteria and renderer tests
  cover routing and byte preservation. Author disagreement: generated output is a boundary even if
  the generator owns it.
- `exec-seam-owns-reap` — reuse of an existing external-effect seam: **extend**
  `clutch/seams.py::ProcessExec` and `SubprocessExec`; consumers can receive per-child resource
  usage through `on_rusage`. Return value and other exec behavior are preserved, with the seam
  owning child reaping. Criteria and process-seam tests cover per-child usage. Author disagreement:
  an optional callback changes the boundary even though existing callers continue to work.
- `cli-group-provider` — CLI behavior and sibling-ticket contract dependency: **replace** old
  `install` and `probe` verbs with `provider install` and `provider probe`, owned by
  `clutch/__main__.py`; operators, guides and tests migrate without aliases. Arguments, processes,
  writes and exits are preserved except the stated road text. Criteria and CLI tests cover the
  transition. It depends on `cli-help-standard`; its ticket also identifies `cli-group-config` as
  the preceding shared parser change. Author disagreement: sequencing a shared edit is not by itself
  a contract dependency; the help standard is the actual dependency.

### Disagreements

The entries record the author judgments above, not a vote to change an owner decision. In particular,
calling the bug fix `none`, treating a shared edit order as a dependency, or omitting a rendering
consumer would disagree with the decisions on preservation, sibling consistency and consumer
closure. The trial found repetition when every unchanged specialized fact was written as “not
applicable”; review instead needed the owner, actual consumers, observable change, compatibility,
criteria and tests, plus the failure, composition or storage facts relevant to each boundary.

### Chosen grammar

The required section is `## Boundary contract`. It contains either the short `none` form or one or
more `### <boundary>` entries. Each full entry uses labeled Markdown list fields: `disposition`,
`owner`, `consumers`, `observable change`, `compatibility`, `acceptance`, `tests`, and
`post-merge source of truth`. The closed dispositions are `reuse`, `extend`, `replace`, `create`,
and `none`; `none` appears as the section's sole disposition followed by `- reason:` with one
concise preservation statement, as in decision 13. `reuse` states no contract change and identifies
composition where relevant. Inputs, outputs, failures, side effects, invariants, ordering,
persistence, atomicity and composition are required when relevant, not as empty fields. Breaking
changes identify old and replacement contracts, consumer migrations, removal and ordering.

A `create` entry also names the closest existing symbols or artifacts in Context, why each cannot
be reused, and its earning reason. The closed reasons are multiple production consumers; an
external-effect fake; a named plugin or provider extension; consolidation of evidenced duplicates;
or a process, storage, package or independently deployed boundary. `none` reasons are documentation
corrections without behavior change; comments, spelling, formatting or metadata only; tests encoding
an existing contract; regeneration with unchanged generator and generated contract; dependency or
version updates proven not to change a consumed boundary; private implementation with callers,
outputs, failures, side effects, construction and formats unchanged; or unreachable private code
with no consumers. Bug fixes and refactors require an explicit restoration or preservation claim.

The section heading, entry headings, labeled common fields, closed dispositions, and presence of a
reason or create justification were consistent enough to check structurally. Path resolution can
check named files; semantic completeness, applicability and whether a reason is true remain review
judgments. Stronger lint waits for recurring findings in deployed use.

### Baseline findings

The historical tickets predate the form. `consumer-error-keeps-capture` shows why a private-looking
callback failure must name the spool reader and restoration obligation; a `none` claim would miss
captured output. `badge-stopped-backlog` shows why the extension reader belongs in consumer closure
when only the snapshot changes. `cli-group-config` shows why a replacement must name old-command
removal and migration, rather than merely describe the new command. `journal-last-transition-helper`
shows why naming the existing inline owners and the preserved lookup result matters when a shared
boundary is created. These are historical risks the form would surface, not assertions that the
merged implementations failed.


### Outcome comparison

Row 153 merged as `adf7d00b` at `2026-11-20T05:08:40+00:00`. The repository journal contained 25 files and 60,701 events from `2026-10-05T07:10:12+00:00` through `2026-11-25T16:09:59+00:00`. The comparison uses `clutch view stats --split 2026-11-20T05:08:40+00:00 --json`.

| Quantity | Before | After |
|---|---|---|
| Settled tickets | 807 (736 merged, 5 already satisfied, 66 rejected) | 279 (201 merged, 1 already satisfied, 77 rejected) |
| Premise failures | 651 (568 implement, 83 requisition, 0 review); 0.885 per merged | 117 (90 implement, 26 requisition, 1 review); 0.582 per merged |
| Rework orders | 24 (17 update, 4 split, 3 escalate); 0.033 per merged | 80 (53 update, 3 split, 24 escalate); 0.398 per merged |
| Review snags mean | 0.165 | 0.204 |
| First-pass yield | 0.662 (66.2%) | 0.493 (49.3%) |
| Duplicate-owner findings | 0; 0.000 per merged | 1; 0.005 per merged |

The after finding was a `scope` snag on `training-export-ticket` at `2026-11-20T06:20:22Z`. Row 153 added no dedicated finding code, so `duplicate_owner_findings` counts `scope` and `acceptance` review snag findings whose text matches `DUPLICATE_OWNER_PATTERN`. These raw windows do not establish causation; rework and review-snag rates also reflect later pipeline changes.

## Measures of success

The policy succeeds when it reduces:

- Implement-time API decisions not present in tickets;
- `premise_failed` outcomes caused by contradictory or missing boundary behavior;
- new wrappers, registries, parsers, codecs, and factories duplicating an existing owner;
- review findings for missed consumers and out-of-fence callers;
- sibling tickets that assume incompatible versions of the same contract;
- tests that bypass the supported seam.

It fails when it increases contract boilerplate without changing those outcomes, causes private
single-caller code to acquire unnecessary protocols, or makes authors specify private algorithms that
Implement should choose.

## Risks

- **Architecture by paperwork.** Agents may add interface classes merely to satisfy the section.
  Mitigation: contract-first language, earning conditions, and explicit exclusion of private details.
- **False confidence from lint.** A valid form may still omit meaningful behavior. Mitigation: state
  that lint proves structure only and retain requisition review as the semantic gate.
- **Search theater.** `searched` may become a list of modules the author did not inspect. Mitigation:
  require exact nearest candidates and concrete incompatibilities, then provide them in Context.
- **Second authority.** A catalog or ticket may compete with code-owned truth. Mitigation: name the
  post-merge owner and generate any discovery view.
- **Host overreach.** Python-specific architecture may leak into every host. Mitigation: keep portable
  rules about boundaries and let host conduct own technology choices.
- **Large tickets.** Fully specifying a broad boundary may reveal that the ticket spans subsystems.
  That is useful evidence to split it, but the resulting dependency chain must preserve one coherent
  contract owner.
- **Preservation loophole.** Authors may overuse `none`. Mitigation: make it a positive preservation
  claim and require reviewer tracing of consumers and formats.
- **Frozen design too early.** Implementing grammar before trials could lock in the wrong abstraction.
  Mitigation: Phase 0 precedes implementation tickets.

## Candidate implementation breakdown

The breakdown records likely change boundaries, not approved work. Author the retrospective trial
first. Its evidence determines the exact grammar used by later tickets; it does not reopen the owner
decisions recorded below.

| # | Candidate stem | Kind | Content |
|---|---|---|---|
| 1 | `boundary-contract-trial` | chore | Apply proposed forms to representative historical tickets and record the chosen vocabulary and exceptions in this plan. |
| 2 | `boundary-contract-authoring` | chore | Shared behavioral rule, host-authoring content, skeleton section, docs, and Author/requisition-review semantics. |
| 3 | `boundary-contract-lint` | feature | Stable structural and referential checks demonstrated by the trial and initial reviews. |
| 4 | `boundary-contract-implementation-review` | feature | Implement premise behavior and diff-review conformity to declared owners and contracts. |

Tickets 3 and 4 depend on 2. Ticket 3 also needs evidence of recurring mistakes from deployed use.

## Design decisions

The owner resolved these decisions one at a time on 2026-11-18. Their explanations remain here so
future tickets preserve the tradeoffs instead of carrying only the final choices.

### 1. What should the section be called? — Decided 2026-11-18

The name teaches authors what the rule is for.

- `Boundary contract` says that the section covers any producer/consumer boundary: Python symbols,
  commands, files, schemas, processes, configuration, and user workflows. It is the most accurate
  name for the design in this plan.
- `Interface contract` is familiar to programmers, but many authors will read it as “add a Protocol,
  abstract class, or public API.” That is exactly the over-abstraction this plan wants to avoid.
- `Change contract` is broad enough for every ticket, but it does not naturally lead an author to
  search for an existing owner or consumer.

Decision: `Boundary contract`. It covers code APIs, commands, files, schemas, processes,
configuration, and workflows without implying that every change needs a language-level interface.

### 2. Should every ticket contain the section? — Decided 2026-11-18

There are two choices. A universal section means every ticket either describes a boundary or writes a
short `none` preservation claim. Lint can then tell the difference between “no boundary changed” and
“the author forgot to consider boundaries.” The cost is one small section in documentation, spelling,
and other low-risk tickets.

A conditional section avoids that boilerplate, but the section disappears in exactly the cases where
an author failed to recognize a configuration key, fixture, file format, or internal consumer as a
boundary. Lint cannot reliably determine that omission after the fact.

Decision: every ticket contains `## Boundary contract`. A ticket that does not change a boundary uses
the deliberately short `none` preservation form. This makes omission mechanically distinguishable
from a considered claim that no boundary changes.

### 3. What facts must every full boundary entry contain? — Decided 2026-11-18

Not every boundary has parameters or exceptions. A JSON file has fields and readers; a CLI has
arguments, output, diagnostics, and exit codes; a callback has inputs, outputs, and timing. Requiring
every specialized field on every kind would create meaningless `not applicable` lines.

The decision is which small common core is always required. A useful common core is disposition,
owner, consumers, observable change, compatibility, acceptance criteria, tests, and canonical
post-merge owner. Inputs, outputs, failures, side effects, composition, ordering, persistence, and
atomicity should be required when they apply to that boundary kind.

Decision: use one small common core: disposition, canonical owner, consumers, observable change,
compatibility, acceptance criteria, contract tests, and permanent post-merge source of truth.
Requisition review also requires inputs, outputs, failures, side effects, ordering, persistence,
atomicity, composition, or other specialized facts when they are relevant to that boundary. Do not
create separate ticket schemas for each boundary kind.

### 4. What is enough reason to create a new interface? — Decided 2026-11-18

If this threshold is too low, agents will manufacture Protocols, factories, and wrapper classes for
single callers. If it is too high, agents will call real external effects directly or duplicate code
because only one production implementation exists.

The proposed earning reasons are: multiple production consumers, a required fake for an external
effect, a plugin/provider extension point, evidenced duplicate behavior, or a process/storage/package
format boundary. The question is whether those cover real work without admitting “it might be useful
later.”

Decision: use these five closed initial reasons: multiple production consumers; a required fake for
an external effect; a plugin or provider extension point; evidenced duplicate behavior that the
change consolidates; or a boundary crossing a process, stored format, package, or independently
deployed component. “It might be useful later” does not qualify. Add another reason only after a real
ticket cannot honestly fit one of the five.

### 5. What proof of reuse search should a `create` entry provide? — Decided 2026-11-18

A raw search transcript is noisy and easy to satisfy without understanding the result. A bare list of
modules is also weak because it does not identify the closest reusable behavior.

The useful evidence is the exact existing symbol or owner that came closest, plus one sentence saying
which required behavior it lacks. Those candidates should appear in Context so the reviewer and
Implement see the same evidence. Search commands may be useful during authoring but do not belong in
the permanent ticket contract.

Decision: a `create` entry names the exact existing symbols or owned artifacts that came closest and
gives a concrete incompatibility reason for each. Those candidates also appear in Context so the
author, reviewer, and Implement inspect the same alternatives. Search commands and raw transcripts
are authoring tools, not permanent ticket content.

### 6. Should the first release block tickets immediately? — Decided 2026-11-18

Immediate blocking gives the rule authority, but the initial form is likely to contain fields that
are redundant or missing. Making it a hard gate before a representative trial could force dozens of
bad tickets to conform to a bad schema.

Review-only deployment is safer but can become advisory indefinitely. The rollout in this plan uses a
middle path: Phase 0 applies the form retrospectively without changing intake; Phase 1 makes the
section structurally mandatory and lets requisition review judge its meaning; Phase 2 adds only lint
checks supported by observed findings.

Decision: use staged enforcement. First run the retrospective trial without blocking. After the trial,
block tickets whose section is missing or structurally malformed while requisition review judges
semantic completeness. Add stronger mechanical lint only for recurring, stable mistakes demonstrated
by deployed tickets.

### 7. How much should lint understand about code symbols? — Decided 2026-11-18

Path checks work across every host language and are easy to trust. Resolving
`clutch/seams.py::ProcessExec` gives better feedback, but Python AST rules do not automatically work
for JavaScript, Rust, schemas, commands, or generated artifacts.

Trying to solve every language in the first lint would turn Clutch into a partial language server.
Limiting lint to paths forever would miss misspelled or deleted owners in the repository where symbol
resolution is reliable.

Decision: use staged symbol support. Begin with path resolution and exact Markdown headings. Add
Python symbol resolution as an earned specialized check after the form is stable. Other host
languages continue to use path checks or host-owned tooling unless repeated evidence earns another
language-specific check.

### 8. What must a breaking contract say about migration? — Decided 2026-11-18

The ticket must not merely label a change “breaking.” Implement needs to know which consumers move,
what old value or path disappears, and when the new form becomes the only form. At the same time,
Clutch's no-dual-path rule forbids automatically adding compatibility shims or deprecation periods.

The minimum useful information is: the old contract, the replacement contract, every known consumer,
the ticket that migrates each consumer, and the point at which the old form is removed. If all
consumers move in one ticket, say so. If they move in dependent tickets, the ordering must make it
impossible to dispatch a consumer before its required contract exists.

Decision: every breaking boundary change states the old contract, its replacement, every known
consumer, the ticket that migrates each consumer, when the old contract is removed, and dependency
ordering when migration spans tickets. This never implies a compatibility shim: consumers move
explicitly and the old path is removed under the existing no-dual-path rule.

### 9. Should Clutch generate an interface discovery catalog? — Decided 2026-11-18

A catalog could let authors find `ProcessExec`, the provider registry, or a snapshot schema without
searching. It would also be another source that can become stale and may encourage authors to search
only the catalog rather than the code.

The current repository already has owner modules, docstrings, Context embedding, and fast text
search. There is no measured incident yet showing those are insufficient. If later tickets repeatedly
create duplicate owners because the existing one was hard to discover, a generated catalog may be
earned. It must derive from code-owned declarations, never be maintained by hand.

Decision: do not build a catalog. The codebase is not large enough to justify another discovery
surface; canonical owner modules, Context, ownership docstrings, and repository search are the paved
road. If the codebase later grows substantially, that would be a new design decision rather than an
automatic follow-up from this plan.

### 10. How much of the rule belongs in the managed host conduct block? — Decided 2026-11-18

Every host needs to know the short behavioral obligation, but ticket content has one authoritative
home in `clutch/docs/host-authoring.md`, and ticket format has one owner in `clutch/tickets.py`.
Copying the full rule into `CORE_TEMPLATE` would create competing versions and consume limited managed
block space.

The core needs only enough language to say: declare the boundary disposition, reuse the canonical
owner, justify a new owner, and do not invent undeclared boundaries. The authoring guide owns the
fields, examples, exceptions, and repair roads.

Decision: `CORE_TEMPLATE` carries one short behavioral paragraph requiring authors to declare the
boundary disposition, reuse the canonical owner, justify a new owner, and forbidding Implement from
inventing undeclared boundaries. `clutch/docs/host-authoring.md` remains the sole owner of fields,
examples, exceptions, and repair roads; `clutch/tickets.py` remains the sole grammar owner.

### 11. Does the filesystem seam own reads as well as writes? — Decided 2026-11-18

The rule currently says filesystem access goes through seams, but the code often injects writes while
reading repository text directly with `Path`. Making every read use `FileSystem` creates one fully
fakeable effect boundary, but it also adds plumbing to pure readers and may make simple parsing code
harder to follow.

The alternative is to define the seam as the owner of durable mutation and nondeterministic directory
observation while allowing a function whose explicit input is a path to read that path directly.
That model is smaller but needs a precise line so code does not bypass atomicity, redaction, or test
isolation by calling `Path` opportunistically.

Decision: use the scoped filesystem rule. All writes, publication, removal, replacement, directory
enumeration, size checks, and mutable engine-state reads go through the filesystem seam. A pure reader
may directly read immutable repository source when the path is an explicit input. Hidden or
opportunistic reads from business logic are not allowed. This preserves atomicity and test isolation
without wrapping every straightforward source read.

### 12. How far should the first code refactor go? — Decided 2026-11-18

The minimum option is 8-12 high-value tickets: move fence semantics to their owner, clarify the main
composition boundaries, fix selected filesystem bypasses, improve owner documentation, and reuse
equivalent fakes. This gives the new ticket rule clear paved roads without reorganizing the entire
engine.

The broader option is 15-22 tickets that also split ambiguous stage and CLI responsibilities and
normalize orchestration composition. That may produce a cleaner architecture, but doing it before the
new rule generates evidence risks speculative movement and conflicts with the smallest-change rule.

Decision: the initial refactor targets the 8-12 high-value tickets: fence ownership, main composition
boundaries, selected filesystem violations, ownership documentation, and equivalent fake reuse. The
broader architecture refactor remains explicit follow-up work. Findings from the deployed boundary
rule determine and justify those later tickets rather than folding speculative movement into the
initial pass.

### 13. How short should the `none` preservation form be? — Decided 2026-11-18

If `none` accepts only that one word, it becomes a loophole. If it requires a long checklist of every
possible boundary, documentation and private implementation tickets will carry more boilerplate than
useful content.

The form should require one reason and a small closed preservation claim appropriate to the change,
for example: “private implementation only; callers, results, failures, side effects, construction,
and persisted formats remain unchanged.” Requisition review checks whether that claim is credible.

Decision: `none` requires one reason plus one concise preservation statement; it never requires the
full boundary field list. Requisition review checks the claim against the affected code and consumers.
The intended shape is:

```md
## Boundary contract

none
- reason: private implementation only; callers, results, failures, side effects, construction,
  and persisted formats remain unchanged
```
