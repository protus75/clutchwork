<!-- clutch:meta
schema: clutch.meta/1.0
kind: plan
purpose: Document agent: plan
relates: [CHANGELOG.md, clutch/docs/host-authoring.md, clutch/docs/host-running.md, clutch/specs/doc/facets/type/roadmap.md, docs/boundary-contract-plan.md, docs/document-agent/audience/ai.md, docs/document-agent/audience/developer.md, docs/document-agent/audience/non-technical.md, docs/document-agent/audience/student.md, docs/document-agent/audience/technical.md, docs/document-agent/audience/user.md, docs/document-agent/format/html.md, docs/document-agent/format/markdown.md, docs/document-agent/format/pdf.md, docs/document-agent/review/AutomatableReview.md, docs/document-agent/review/BuildItReview.md, docs/document-agent/review/CompressionReview.md, docs/document-agent/review/CutReview.md, docs/document-agent/review/KillReview.md, docs/document-agent/review/evidence/OutcomeReview.md, docs/document-agent/review/evidence/SeedPlanDiagnosis.md, docs/document-agent/theme/dark.css, docs/document-agent/theme/dark.md, docs/document-agent/theme/light.css, docs/document-agent/theme/light.md, docs/document-agent/tone/default.md, docs/document-agent/tone/examples.md, docs/document-agent/type/api.md, docs/document-agent/type/architecture.md, docs/document-agent/type/blog.md, docs/document-agent/type/overview.md, docs/document-agent/type/plan.md, docs/document-agent/type/release-notes.md, docs/document-agent/type/seed.md, docs/document-agent/type/spec.md, docs/document-agent/type/whitepaper.md, docs/evidence-trail-plan.md, docs/how-clutch-works.md, docs/roadmap.md, docs/training-data-plan.md]
owner: engine
verified: 62a64dee
hash: 7af2625d4ea4fe11646ef089fe93bdd539438b9f5fd0f0a6362288aa7af481c0
-->
# Document agent: plan

A document agent for clutch that creates, reviews, and transforms documents. Each request picks one value from six dimensions: **Type**, **Audience**, **Format**, **Review**, **Tone**, and **Theme**. Each dimension is a list of files that can be extended. One canonical Markdown document (usually a Plan) is the source, and versions for other audiences and formats are derived from it. When a derived version is edited, the edit is folded back into the canonical document and then passed on to the other derived versions, so the set does not drift apart. Reviews run as isolated agent panels with a synthesis that checks the findings against the document, following the owner's existing review prompts.

## Status

Draft plan. Nothing in it is in effect and no ticket is authored. Written 2026-11-13 at commit `0895b5d4`; revised 2026-11-13 at commit `80b76d5d` to take in the owner's review prompts in [review/](review/) and for `docs/roadmap.md`.

## Roadmap

Release 0.8.0, last (`docs/roadmap.md` rows 75-86). Needs from other plans: `evidence-envelope` (0.4.0), so an isolated call leaves a record with `repo: null` and `conduct_file: null` (roadmap decision 3); `fence-overlap` (0.5.0) for the Automatable lens's overlap estimate; `panel-combiners` (0.6.0, `docs/stage-panels-plan.md`), which is the one fan-out-and-combine mechanism the review runner stands on (roadmap decision 14); `context-suggest` (0.6.0, `docs/annotations-index-plan.md`) for `doc draft --from <topic>`. Nothing depends on this plan. Shared budgets: one new config block, named `documents` (not `docs`: that is a verb and the `clutch/docs/` directory; roadmap decision 6); no CORE_TEMPLATE text. Its first real use is reviewing the other plans, which is why it is last: by then they have tickets and run history behind them.

## What it is for

1. **From conversation or loose notes to a plan.** Turn a chat or "vibe" session, or several scattered Markdown files, into one canonical Plan with a fixed shape.
2. **One source, many readers.** Derive an overview for non-technical readers, an API reference for developers, a seed for ticket authoring, or a blog post, all from the same Plan, and render them as Markdown, HTML, or PDF.
3. **Reviews you can act on.** Run a lens as several isolated reviewers, then verify and merge their findings. A finding that several reviewers reach independently is treated as real. A finding from one reviewer is a lead to check.
4. **No drift.** Every derived document records which canonical sections it was built from. When the canonical document changes, clutch says which derived documents are stale. When a derived document is edited, the edit is proposed back into the canonical document instead of being lost or contradicting it.
5. **Plans organize other work.** A Plan's ticket breakdown is the bridge to clutch tickets (through a Seed), and its sections are the anchors that derived works cite.

## Current state

- `clutch/specs/ask/` holds operator prompt templates rendered by `clutch prompt <kind>` (`clutch/ask.py`, closed `KINDS` tuple). The extension opens one in a Claude Code chat ("Ask Claude: drain loop"). That is the existing route for interactive, guided work.
- Driver specs in `clutch/specs/` run headless through one driver (`clutch/driver.py`), with routing by `(tier, surface)` and a fallback to the `review` row for an unrouted surface (`clutch/providers.py:104`). Every surface except Implement is read-only. The model returns text, and the engine writes the files.
- Read-only surfaces are **not isolated**. Claude runs with `--tools Read Grep Glob LS` in the repo (`ClaudeAdapter.argv`). Codex runs `--sandbox read-only` in the repo. A reviewer can browse the repository, which the owner's review prompts forbid ("Your only input is the document").
- Specs always load from the engine. Host material enters a prompt only inside `<<clutch-data:...>>` blocks (`ask_notes` is the precedent). Config load refuses `review.surfaces` (host review prompts).
- The [review prompts](review/) have been used in manual seed-plan reviews. In one Cut review, all three reviewers flagged a spend ceiling. The synthesis checked the strongest reason to keep it against the plan: both configured providers used flat subscriptions. It recommended deferring the ceiling until the first metered provider and moving failure handling earlier. The agreement count, the check against the document, and the proposed edit all belong in the report.
- No document tooling exists in clutch: no Markdown-to-HTML renderer, no PDF path, no theme CSS.

## Departures from the design record

| Record says | This plan | Why |
|---|---|---|
| §18.1 refuses "metadata taxonomies" and "doc tags" | Facets (six closed dimensions) and `docset.yaml` manifests | The owner asked for the six dimensions on 2026-11-13. Each dimension is a closed allowlist of files, not a free tag space, and the manifest records provenance (which sections a derived document came from), not classification. The refusal's target was taxonomy for its own sake; this is the minimum that makes fold-back and staleness mechanical |
| D7-style "never act on estimate-vs-estimate" | The Automatable lens compares dry-run ticket fences with `fences_overlap` | It reports an estimate as a finding for the owner, never acts on it |

`CLUTCH_PLAN.md` stays frozen. The tickets add a "Documents" section to `docs/how-clutch-works.md` and a config row.

## Target design

### 1. Dimensions and facets

Each dimension value is a **facet**: one Markdown file with frontmatter, kept under `clutch/specs/doc/facets/<dimension>/<value>.md`. The set of files is the closed list (an allowlist). Adding a value means adding a file and its test pin.

| Dimension | Initial values | Kind | Applies at |
|---|---|---|---|
| Type | `plan`, [roadmap](../../clutch/specs/doc/facets/type/roadmap.md), `seed`, `overview`, `architecture`, `api`, `spec`, `whitepaper`, `blog`, `release-notes` | prompt facet: required sections and their order, what each section is for | create, derive |
| Audience | [technical](audience/technical.md), [non-technical](audience/non-technical.md), [ai](audience/ai.md), [user](audience/user.md), [developer](audience/developer.md), [student](audience/student.md) | prompt facet: assumed knowledge, vocabulary, what to explain, what to leave out | create, derive |
| Tone | [default](tone/default.md), [examples](tone/examples.md) | prompt facet. `examples` takes example files as data: "match the voice, sentence length, and structure; never copy content" | create, derive |
| Review | `scope`, `viability`, `buildability`, `automatable`, `compression` | lens facet (section 4): roles, run shape, prompts, output schema, verdict set | review |
| Format | [markdown](format/markdown.md), [html](format/html.md), [pdf](format/pdf.md) | render facet, mechanical, no model | render |
| Theme | [light](theme/light.md), [dark](theme/dark.md) | render facet: a CSS token file, used by `html` and `pdf` only | render |

Choose one value per applicable dimension. Type supplies the document structure, Audience sets assumed knowledge and explanatory detail, and Tone governs expression. Together they preserve the source’s obligations, uncertainty, protected text, and the fidelity rules in section 5. For example, a developer release note can show the changed signature and migration call; a user release note for the same change can describe the affected workflow and required action. Both must agree on release membership and compatibility.

Section 4.1 links the five Review prompts and identifies their roles and verdicts. Format consumes the resulting Markdown. HTML and PDF use the same theme roles with either the [light tokens](theme/light.css) or the [dark tokens](theme/dark.css). The linked audience, tone, format, and theme files are first-pass design examples alongside the Type prompts.

The first-pass Type prompts below are design examples. Their project references explain the choices in each prompt. At review time, an isolated panelist works from the generated document.

| Type prompt | What it draws from the project |
|---|---|
| [Roadmap](../../clutch/specs/doc/facets/type/roadmap.md) | Synthesizes local plans into the roadmap read by the driver. |
| [Plan](type/plan.md) | The [roadmap](../roadmap.md) ties phases to entry conditions and observable exits. [Cut](review/CutReview.md) tests scope against the plan’s metric, [Kill](review/KillReview.md) tests the premise, and [Buildability](review/BuildItReview.md) exercises one named phase. |
| [Seed](type/seed.md) | The [host authoring guide](../../clutch/docs/host-authoring.md) owns fences, dependency semantics, acceptance evidence, and the authoring handoff. Section 4.3 describes the Automatable lens ([AutomatableReview.md](review/AutomatableReview.md)). |
| [Overview](type/overview.md) | Section 5 defines audience-change fidelity. The [running guide](../../clutch/docs/host-running.md) supplies operator actions and outcomes when explaining Clutch. |
| [Architecture](type/architecture.md) | The [boundary-contract plan](../boundary-contract-plan.md) identifies owners and consumers. [How Clutch works](../how-clutch-works.md) distinguishes authoritative state, effects, diagnostics, and projections. |
| [API](type/api.md) | The [boundary-contract plan](../boundary-contract-plan.md) defines the producer and consumer contract. A named phase gives the [Buildability dry run](review/BuildItReview.md) a scope for writing stubs from the reference alone. |
| [Spec](type/spec.md) | [Compression and fidelity review](review/CompressionReview.md) preserves normative force, headings, protected regions, and unresolved differences. Section 5 defines promotion. |
| [Whitepaper](type/whitepaper.md) | The [evidence trail](../evidence-trail-plan.md) and [training-data plan](../training-data-plan.md) distinguish captured observations, derived records, outcome labels, and proposed evaluations. |
| [Blog](type/blog.md) | Section 5 governs fidelity when changing audience. For a run narrative, [How Clutch works](../how-clutch-works.md) identifies the artifacts that support claims about what happened. |
| [Release notes](type/release-notes.md) | The [changelog](../../CHANGELOG.md) identifies release entries. [How Clutch works](../how-clutch-works.md) distinguishes a local release tag from publication. |

Facet frontmatter:

```yaml
---
facet: audience/non-technical
version: "1.0"
summary: Readers who use the result but do not build it.
aliases: []                        # e.g. review/scope has [cut]
applies_to: [create, derive]       # or [review], or [render]
requires: []                       # e.g. theme facets: requires format in [html, pdf]
---
```

- **Model facets** (Type, Audience, Tone, Review) change the prompt. **Render facets** (Format, Theme) change only the mechanical output. The model always writes Markdown.
- A facet that does not apply to an operation is refused with a paved road.
- **Host extension:** `documents.facets_dir` points at host facet files with the same frontmatter. They enter the prompt as `<<clutch-data:facet>>` blocks inside the engine's surface frame. Whether host *lenses* are allowed is Open decision 2.

### 2. Doc sets: one canonical document and its derived versions

A **doc set** is a directory with a manifest:

```
docs/plans/parallel-tickets/
  docset.yaml
  plan.md                         # canonical
  overview.non-technical.md       # derived
  overview.non-technical.html     # rendered
  spec.md                         # derived by the compression lens, promoted on LOSSLESS
  reviews/2026-11-13-scope.md     # review report
```

`docset.yaml` (schema `clutch.docset/1.0`, strict writer and tolerant reader, as in `docs/evidence-trail-plan.md` §5):

```yaml
schema: clutch.docset/1.0
canonical:
  path: plan.md
  facets: {type: plan, audience: developer, tone: default}
  sections: {status: 3f9a..., current-state: 81c2..., target-design: 0d7e...}   # heading slug -> content hash
derived:
  - path: overview.non-technical.md
    facets: {type: overview, audience: non-technical, tone: default}
    renders: [{format: html, theme: light, path: overview.non-technical.html}]
    built_from: {commit: 0895b5d4, sections: {target-design: 0d7e..., risks: 77aa...}}
    hash: 5be1...            # this file's hash when clutch last wrote it
    fidelity: {verdict: LOSSY-MINOR, report: reviews/2026-11-13-fidelity-overview.md}
```

- **Section identity** comes from heading slugs. The owner's compression prompt already requires that "section numbers and heading text stay exactly as in the original", so headings are a stable key across derived versions.
- **`clutch doc status`** is mechanical and reports one state per derived document: `current`, `stale` (a canonical section it used changed), `diverged` (edited after clutch wrote it), or `stale+diverged`.
- `derive` refuses to overwrite a `diverged` file. The paved road is `clutch doc fold <path>`, or `--discard-edits` to throw the edits away on purpose.

### 3. Surfaces and isolation

| Surface | Spec | Purpose |
|---|---|---|
| `doc_draft` | `clutch/specs/doc/draft.md` | sources + Type, Audience, and Tone facets → canonical Markdown + open questions |
| `doc_derive` | `clutch/specs/doc/derive.md` | canonical + target facets → derived Markdown + the sections it used |
| `doc_review` | `clutch/specs/doc/lens.md` | one generic frame. The lens facet supplies the role prompt (cut agent, synthesis, compressor, fidelity, ...) and the reply schema. Named `lens.md`, not `review.md`, because `clutch/specs/review.md` exists (roadmap decision 6). |

Every file under `clutch/specs/doc/` carries the spec frontmatter that `tests/unit/test_specs.py:24` checks on everything under `clutch/specs/`, and loads through `clutch/specs/__init__.py` like the eight driver specs; facets and themes are data files the specs embed, not specs, and live under `clutch/specs/doc/facets/` and `themes/` with the walker told to skip them.
| `doc_fold` | `clutch/specs/doc/fold.md` | canonical + diverged derived document + its diff → proposed canonical patch, with changes in meaning separated from changes in style |

**Isolation is a property of the call, not of the prompt.** Every lens prompt says the agent's only input is the document, with "no knowledge that other agents exist". Today's read-only surfaces can read the whole repository, so the doc surfaces get a new isolated mode:

- The call runs with its working directory set to a fresh scratch directory under `state_dir/doc-scratch/<call>/`. That directory holds only the files the role is allowed to see: the document for a panelist; the document and the panel reports for a synthesis; the original and the draft for a fidelity auditor.
- Claude gets `--tools Read Grep Glob LS` scoped to that directory, and Codex gets `--sandbox read-only` with that directory as its working directory. The adapter's `writes` decision (`req.surface in WRITING_SURFACES`, `clutch/providers.py:321`; `WRITING_SURFACES = {"implement"}` at line 29) stays false because no `doc_*` surface is a writing surface. A new `isolated` field on `LLMRequest` (`clutch/llm.py:15`) selects the scratch directory as the working directory, a third source beside the worktree (writing calls) and the repo (`providers.py:338`).
- No conduct file is loaded: the scratch directory has no `CLAUDE.md` or `AGENTS.md`, by design, since a panelist must see only the document. The evidence record says so (`isolated: true`, `conduct_file: null`, `repo: null`; `docs/evidence-trail-plan.md` §2), so a reader can tell these calls from every other call.
- The prompt names no other agent, no prior run, and no review history. No earlier report from the doc set's `reviews/` directory is ever placed in a panelist's scratch directory. That prevents anchoring, as the owner's prompts require.
- The scratch directory is removed after the call, and the evidence record (`docs/evidence-trail-plan.md`) keeps what the call saw.

Reply gates (fail closed, with re-prompting as the driver does now):

- `doc_draft` / `doc_derive`: every required section of the Type facet is present and in order. Every cited canonical section exists.
- `doc_review`: the reply matches the role's declared schema. Every finding cites a heading or line that exists in the document ("no finding without a location"). The verdict, when the role has one, is in the lens's closed verdict set.
- Synthesis roles: **accounting gate.** Every panel finding id appears exactly once: in a cluster, the findability list, the low-confidence tail, or `dropped` with a reason (for example, single-reviewer opinion). A synthesis that loses a finding without saying so is refused.
- `doc_fold`: the patch applies cleanly to the canonical document at its current hash.

### 4. Review lenses

#### 4.1 Lens catalog (from the owner's prompts)

| Lens id | Source prompt | Alias | Question | Run shape | Verdicts |
|---|---|---|---|---|---|
| `scope` | [CutReview.md](review/CutReview.md) | `cut` | What does the document specify that no stated goal justifies, and what effort is in the wrong order? | 3 isolated cut agents → 1 synthesis | LEAN / TRIMMABLE / GOLD-PLATED, plus NO-METRIC |
| `viability` | [KillReview.md](review/KillReview.md) | `kill` | Should this be built as written? | 3 isolated kill agents → 1 synthesis | VIABLE / VIABLE-WITH-CHANGES / NOT VIABLE AS WRITTEN |
| `buildability` | [BuildItReview.md](review/BuildItReview.md) | `build-it` | What does an implementer have to invent, because the document does not decide it? | 3 isolated dry-run implementers for `<PHASE_SCOPE>` → 1 synthesis | SELF-CONTAINED / GAPS-FIXABLE / NOT SELF-CONTAINED |
| `compression` | [CompressionReview.md](review/CompressionReview.md) | | Rewrite in specification form with nothing lost | 1 compressor (writes a draft) → 1 isolated fidelity auditor | LOSSLESS / LOSSY-MINOR / LOSSY |
| `automatable` | [AutomatableReview.md](review/AutomatableReview.md) | | Could an AI pipeline carry the document to merged code with no human decisions? | 3 isolated dry-run *ticket authors* → mechanical lint → 1 synthesis | AUTOMATABLE / AUTOMATABLE-WITH-GATES / NOT AUTOMATABLE AS WRITTEN |

What every lens shares, taken from the prompts:

- **Panelists use identical prompts and are fully isolated.** "Identical prompts keep the convergence statistic clean."
- **The synthesis re-reads the document and checks each cluster.** When the document does answer an issue that reviewers missed, the cluster moves to a **FINDABILITY** list: the answer exists, but sits where a reader would not look. That is a structure defect, not a content gap.
- **Ranking:** blocking findings first (NOT VIABLE grounds, BLOCKED, NO-METRIC), then 3/3, then 2/3. Single-reviewer findings labelled opinion are dropped. Other single-reviewer findings go to a low-confidence tail.
- **Disagreement is reported, not averaged.** Divergent value judgments go to the owner.
- **High reasoning effort** for every role (`agent_effort: high`).
- **The review recommends, and the owner decides.** No lens commits code or edits the canonical document. Its findings become proposed edits through the same accept flow as fold-back (section 5).
- **A short report is a valid result.** "On a lean document, few findings is a valid outcome, not a failed run."

#### 4.2 Lens facet format

A lens facet carries the source prompt text verbatim, split into roles, with the placeholders made explicit:

```yaml
---
facet: review/buildability
version: "1.0"
aliases: [build-it]
source: docs/document-agent/review/BuildItReview.md
params: {PLAN_PATH: document, PHASE_SCOPE: required}   # refused with a paved road when missing
stages:
  - {role: dry_run, count: 3, isolated: true, sees: [document]}
  - {role: synthesis, count: 1, isolated: true, sees: [document, stage.0]}
verdicts: [SELF-CONTAINED, GAPS-FIXABLE, NOT SELF-CONTAINED]
---
## Role: dry_run
<the "Dry-run agent prompt (verbatim)" section>
## Role: synthesis
<the "Synthesis agent prompt (verbatim)" section>
## Schema: dry_run
<ledger entry fields and closed classes: missing / ambiguous / contradictory / deliberate-freedom; BLOCKED list>
```

- The prompt text stays the owner's. clutch adds only the output schema, so "output returns as structured data" becomes a gated JSON reply.
- `<PLAN_PATH>` becomes the document's file name inside the scratch directory. `<SPEC_PATH>` (compression) becomes the draft the engine writes from the compressor's reply, since agents never write files.
- `count` is configurable per run (`--panel N`, minimum 2). The default stays 3, as the prompts specify.
- `compression` declares a different shape: `compressor` (count 1, returns the spec text + ledgers + metrics) then `fidelity` (count 1, sees the original, the draft, and the compressor's ledger and duplicate map, but not its reasoning). The fidelity auditor's mechanical checks ("check these mechanically with diff") run in the engine: protected regions (fenced code, commands, extraction-marker blocks) are compared byte for byte, and those results are given to the auditor as facts.
- [OutcomeReview.md](review/evidence/OutcomeReview.md) and [SeedPlanDiagnosis.md](review/evidence/SeedPlanDiagnosis.md) are **evidence lenses**: they read local run evidence (plan revisions, commit records, tickets), not one document. They are out of v1. Section 4.4 says how they connect later.

#### 4.3 The AI Automatable lens, and how it compares with BuildIt

**What it tests.** BuildIt asks whether the document *determines* every decision an implementer needs. Automatable asks a different question: once decided, can the work be *carried out and verified by machine*, as a set of clutch tickets that go through Implement, Check, Review, and Merge with no human beyond `confirm`? A document can be fully self-contained and still not be automatable: "the dashboard feels responsive" is fully decided and has no oracle. It can also be automatable while leaving free choices an AI is allowed to make.

**How it is fully automated.** Its implementer role-plays clutch's *Author*, not a human engineer. It produces artifacts clutch can already check without a model:

1. **3 isolated dry-run authors.** Each sees the document plus the authoring contract the real executor obeys: `clutch/docs/host-authoring.md` and the ticket skeletons. That contract is to Automatable what "the document's implementation language" is to BuildIt. It is the target machine's rules, not project context. No repository, no history, no knowledge of the other agents. For `<PHASE_SCOPE>`, each returns:
   - a **ticket set** in clutch format (frontmatter, Goal, Scope, Scope fence, Acceptance criteria, Verification, Depends on);
   - an **oracle ledger**: for every acceptance criterion, how a machine decides it (`test`, `command`, `path-exists`, `lint`, `none`). `none` means a person has to decide;
   - a **human-gate ledger**: every step the agent could not hand to an agent, in closed classes: `credential` (accounts, keys, payment), `external` (third-party approval, hardware, a service that does not exist yet), `judgment` (taste, UX feel, legal, business priority), `data` (inputs the document assumes but nothing produces), `irreversible` (a production action with no rollback);
   - an **invented-decisions ledger**, with BuildIt's classes, so the two lenses can be compared directly.
2. **Mechanical stage, with no model.** The engine writes each ticket set into a scratch `tickets/` directory and runs the real ticket checks that `clutch lint` runs (`validate_ticket`, then `lint_findings`, both in `clutch/tickets.py`) on every ticket. The checks cover the grammar, required sections, the fence covering every carried path, `Depends on` naming tickets in the set, and acyclic ordering. When the document belongs to an existing host repo, `## Context` entries are also resolved against that repo. Results per ticket, plus counts (tickets, criteria by oracle class, estimated fence overlap from `docs/parallel-tickets-plan.md` §2), go to the synthesis as facts. `--deep` also runs `requisition_review` on each ticket. It is expensive and opt-in.
3. **1 synthesis.** It re-reads the document, then ranks:
   - human gates found by 3/3 and then 2/3 agents (verified against the text; a gate the document does settle goes to FINDABILITY);
   - criteria with oracle `none` that several agents reached for the same deliverable;
   - **decomposition divergence**: when three authors split the same deliverable in three different ways, the document does not determine the work's structure. That is a finding even when every ticket passes lint;
   - recurring lint failures on the same deliverable across agents, which point at a document gap and not at one agent's slip;
   - ordering disagreements (different `Depends on` graphs for the same deliverables).

   It also reports an **automation ratio**: the share of the document's deliverables covered, in at least 2 of the 3 sets, by lint-clean tickets whose criteria all have an oracle other than `none`.

   Verdict:
   - AUTOMATABLE: no verified human gate, ratio 1.0;
   - AUTOMATABLE-WITH-GATES: every verified gate is named and can be placed as a human ticket or a `confirm` point ahead of the tickets that need it;
   - NOT AUTOMATABLE AS WRITTEN: a core deliverable has no oracle in any set, or a verified gate sits in the middle of the work where no ordering can isolate it.

**Disposition.** As in BuildIt, the ticket sets are measurement instruments and are discarded by default. The owner may promote the synthesis's consensus set into a Seed (section 7), but it still goes through the real authoring flow. Findings become document edits: add the oracle, name the gate and its owner, fix the decomposition.

**Comparison:**

| | BuildIt (`buildability`) | AI Automatable (`automatable`) |
|---|---|---|
| Question | Does the text determine every decision? | Can a machine carry out and verify the work? |
| Role-played implementer | A human engineer writing skeletons | clutch's Author writing tickets |
| Input beyond the document | none | the authoring contract (guide + skeletons) |
| Product | module skeleton, interface stubs, invented-decisions ledger, BLOCKED list | ticket set, oracle ledger, human-gate ledger, invented-decisions ledger |
| Mechanical check | none: everything is model judgment | real ticket lint on every ticket, plus counts |
| Convergence signal | the same decision invented by k/3 agents | the same gate, missing oracle, lint failure, or split found by k/3 agents |
| Catches that the other misses | interface and data-shape gaps, contradictions between passages | unverifiable criteria, human-only steps, work that cannot be split into tickets under the diff budget, unclear ordering |
| Misses | whether the result can be checked or run unattended | design gaps the authors filled from the authoring guide's defaults |
| Cost | 4 calls | 4 calls + one lint per ticket (+ requisition reviews with `--deep`) |
| Can be checked against reality later | by OutcomeReview, by hand | by `docs/training-data-plan.md` data: predicted gates and ticket counts against the journal's actual parks, confirms, and attempts |

Run BuildIt first. Automatable assumes the decisions are settled, so its findings on an unsettled document mostly repeat BuildIt's gaps. The full prompt is in [AutomatableReview.md](review/AutomatableReview.md).

#### 4.4 Later: evidence lenses

OutcomeReview's **evidence overlay** stamps each document-review cluster CONFIRMED, UNCONTRADICTED, WEAKENED, or CONTRADICTED against what real runs did. "Convergence ranks attention; evidence decides." For a host that runs its plan through clutch, the run evidence is already in its own journal and tickets: attempts, parks, confirms, conflict facts, plus the evidence trail once it ships. A later `outcome` lens can read a local snapshot of those records. Its trigger is the first plan that has both a review report and a finished clutch run.

### 5. Fold-back, review dispositions, and fidelity

1. `clutch doc status` reports a derived document as `diverged`, or a review report proposes edits.
2. `clutch doc fold <path>` (or `clutch doc apply <report>`) writes a proposed patch to the canonical document, plus a note on what was not applied and why.
3. The owner accepts the patch, edits it, or rejects it. Accepting applies it and updates the section hashes. Refuse-class cuts from the `scope` lens go to the document's refusals list, as [CutReview.md](review/CutReview.md)'s disposition requires, so the cut scope does not come back.
4. Derived documents built from changed sections become `stale`. `clutch doc derive --stale` rebuilds them.

**Fidelity as a gate on derivation.** The compression lens's fidelity role is reused to check derived documents:

- For a derive that changes only form (`spec`, or the same audience), the full class list applies (DROPPED, ALTERED, INVENTED, RESOLVED AMBIGUITY, VERBATIM VIOLATION, BROKEN REFERENCE), and a `spec` is promoted only on LOSSLESS plus a human-reviewed diff, as in [CompressionReview.md](review/CompressionReview.md).
- For a derive that changes audience (a non-technical overview drops detail on purpose), only INVENTED, ALTERED, and RESOLVED AMBIGUITY count. A derived document may leave things out, but never add or change facts.
- The verdict is recorded in `docset.yaml` (`fidelity`).

### 6. Guided drafting: from chat to a plan

- **Interactive.** `clutch prompt doc-plan [files...]` (template `clutch/specs/ask/doc-plan.md`) opens a Claude Code chat that walks the operator through the Plan Type's sections, one question at a time for what the sources leave open. It ends by writing the doc set through `clutch doc draft`. The extension gets an "Ask Claude: draft a plan" menu item.
- **Headless.** `clutch doc draft --type plan --audience developer --from a.md b.md notes/*.md --out docs/plans/<name>/`. Anything the sources leave open goes into `## Open decisions`, never into an invented answer.
- The `plan` Type facet requires what the lenses need in order to work at full strength: stated goals and an **optimization metric** (otherwise `scope` leads with NO-METRIC), a refusals list, implementation phases (BuildIt's `<PHASE_SCOPE>` names one), and a ticket breakdown.

### 7. Plans and Seeds lead to tickets

- The `seed` Type, derived for Audience `ai`, turns each ticket row into what an authoring session needs: fence files, acceptance criteria, and where each rule lives. An `automatable` consensus set can be its starting point.
- Tickets are still authored the one way clutch allows: `clutch new` + `clutch/docs/host-authoring.md` + `clutch lint` + `clutch review`. The document agent never writes `ticket.md` into `tickets/`.

### 8. Render

- Markdown to HTML in pure Python with a new dependency (`markdown-it-py`, with tables, footnotes, and heading anchors). The theme's CSS is embedded inline, so the output is a single file.
- Themes are `clutch/specs/doc/themes/light.css` and `dark.css` (CSS custom-property tokens). Host themes come from `documents.facets_dir/theme/`.
- PDF goes HTML to PDF through a host-declared argv (`documents.render.pdf`), run through the exec seam and the parallel plan's host-command lock when that exists. When none is configured, `--format pdf` is refused with a paved road naming the key.
- Mermaid stays as code blocks in v1.

### 9. Config

```yaml
documents:
  facets_dir: null          # host facet extensions; injected as data
  review:
    panel: 3                # default panelists per lens (min 2)
    diverse: false          # rotate panelists across the route's candidates
  render:
    pdf: null               # argv list
```

A new `Documents` model in `clutch/config.py` with a default, so existing configs load unchanged. The block is `documents`, not `docs`, because `docs` is already a verb (`clutch/__main__.py:311`) and the `clutch/docs/` guide directory; `documents.review` sits beside the top-level `review` block and shares nothing with it.

## Where each piece lives

| Piece | Home |
|---|---|
| Facet and lens files (engine-owned; lens prompt text from the owner's review files) | `clutch/specs/doc/facets/<dimension>/<value>.md` |
| Surface specs | `clutch/specs/doc/{draft,derive,lens,fold}.md` |
| Config | `clutch/config.py` (`Documents`) |
| Interactive prompt | `clutch/specs/ask/doc-plan.md`, added to `KINDS` in `clutch/ask.py` |
| Isolated scratch working directory for a call | `clutch/providers.py` (`isolated` request field), `clutch/llm.py` (`LLMRequest`) |
| Facet registry, docset schema, section hashing, status | new `clutch/docs_agent/` package (`facets.py`, `docset.py`) |
| Lens runner (stages, panel, accounting gate, engine-side mechanical checks), fold, apply | `clutch/docs_agent/review.py`, `fold.py` |
| Dry-run ticket lint for `automatable` | `clutch/docs_agent/review.py` calling `validate_ticket` and `lint_findings` in `clutch/tickets.py` (no copy of the rules) |
| Render and themes | `clutch/docs_agent/render.py`, `clutch/specs/doc/themes/` |
| Verbs `doc draft / derive / review / fold / apply / render / status / facets` | `clutch/__main__.py`, plus `./dev.py` subcommands |
| Extension menu items | `vscode-clutchwork/` (draws snapshot fields and runs the verbs) |
| Operator docs | `docs/how-clutch-works.md`, new section "Documents" |

## Ticket breakdown

Each ticket puts its tests in new files (`docs/parallel-tickets-plan.md` §7).

| # | Stem | Kind | P | Depends on | Content |
|---|---|---|---|---|---|
| 1 | `doc-facet-registry` | feature | P2 | | Facet format (with `aliases`, `params`, `stages`, `verdicts`), loader, validation, `clutch doc facets`. Type, Audience, Tone, Format, and Theme facet files. |
| 2 | `docset-manifest` | feature | P2 | | `clutch.docset/1.0`, section hashing, `clutch doc status`. |
| 3 | `isolated-readonly-call` | feature | P2 | `evidence-envelope` | `isolated` request mode: scratch working directory with only the declared files, for Claude and Codex; the evidence record carries `isolated`, `conduct_file: null`, `repo: null`. Tests prove a panelist cannot read a repo file. |
| 4 | `doc-review-runner` | feature | P2 | 1, 3, `panel-combiners` | Generic `doc_review` surface, stage runner on `clutch/panel.py` (the lens's `stages` map onto panel members and combiners; the synthesis role is a model combiner the lens supplies), schema and verdict gates, accounting gate, report. |
| 5 | `doc-lenses-from-owner-prompts` | feature | P2 | 4 | `scope`, `viability`, `buildability`, and `compression` lens facets from the prompt files in [review/](review/), with schemas. Engine-side byte-identity checks of protected regions for `compression`. |
| 6 | `doc-lens-automatable` | feature | P2 | 4, `fence-overlap` | [AutomatableReview.md](review/AutomatableReview.md) as a lens facet, the mechanical ticket-lint stage, the automation ratio, the fence-overlap estimate, and `--deep`. |
| 7 | `doc-derive-fidelity` | feature | P2 | 2, 5 | `doc_derive`, fidelity gate by derive class, `fidelity` recorded in `docset.yaml`. |
| 8 | `doc-fold-apply` | feature | P2 | 2, 7 | `doc_fold`, `doc apply <report>`, accept flow, refusals-list placement, `derive --stale`. |
| 9 | `doc-render` | feature | P2 | 1 | Markdown to HTML with themes, PDF through the configured argv, the `documents` config block. |
| 10 | `doc-draft` | feature | P2 | 1, 2 | `doc_draft` (headless) and the `doc-plan` ask prompt (interactive). |
| 11 | `doc-extension-menu` | feature | P3 | 8, 10 | Snapshot fields for doc sets and their states, and menu items. |

Tickets 1, 2, and 3 touch separate files and suit a first parallel trial.

## Risks

- **Fold-back or review edits that change meaning without notice.** The owner approves every canonical patch. Nothing applies automatically.
- **Cost.** One lens is 4 calls (3 + synthesis). All five lenses are 18 calls plus lint. Lenses are chosen for each run, with no "all" default.
- **Model diversity and the convergence statistic.** Identical prompts on one model measure agreement across samples. Panelists on different models measure agreement across models, which is a stronger signal (SeedPlanDiagnosis: "a defect both providers hit is almost certainly a real seed defect"). The two counts are not comparable, so every report records the model that served each panelist, and `diverse` is off by default.
- **The Automatable lens judges against the authoring guide as it stands.** When the guide changes, old automatable reports become stale. Each report records the guide's hash.
- **Host lenses are host instructions.** They cut against the current refusal of `review.surfaces` (Open decision 2).

## Open decisions

Decisions taken on 2026-11-13 and 2026-11-14 are marked; `docs/roadmap.md` §6 is the record. Nothing here remains open.

1. **`diverse` panels by default?** Decided 2026-11-13: off by default, so convergence counts compare with the owner's earlier manual runs; `--diverse` on a run rotates panelists across the route's candidates.
2. **Host-defined lenses and facets.** Decided 2026-11-13: allowed, as data blocks inside the engine frame through `documents.facets_dir`. The owner's lenses ship as engine facets either way. The refusal of `review.surfaces` for code review stays.
3. **Verbs only, or a `doc` ticket kind too?** Decided 2026-11-13: verbs only for v1; a `doc` kind is the follow-up if doc sets start being changed by the drain.
4. **Where doc sets live.** Decided 2026-11-14: any `docs/<name>/` with a `docset.yaml`, found by search; no registry file.
5. **Panel size.** Decided 2026-11-14: default 3, minimum 2; `--panel 1` is refused because a single reviewer has nothing to converge with. Promoting an `automatable` consensus ticket set into a Seed stays an explicit owner step, never automatic.
6. **Move today's plans into doc sets** once tickets 1 and 2 merge? Decided 2026-11-14: yes; `plans-into-docsets` (roadmap row 76) runs `scope` and `buildability` on each as the first real use and is 0.8.0's ship gate.

## Appendix: draft `AutomatableReview` prompt

[AutomatableReview.md](review/AutomatableReview.md) contains the full dry-run author and synthesis instructions.
