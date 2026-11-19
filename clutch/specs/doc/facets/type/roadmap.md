---
facet: type/roadmap
version: "1.0"
summary: Synthesize qualified host plans into a maintained roadmap.
aliases: []
applies_to: [create, derive]
requires: []
---

# Roadmap Type

Create or derive `docs/roadmap.md` as the cross-plan ordering, not a replacement for design in the source plans. Cite plan sections and current evidence for every claim; distinguish observed facts from proposals. Record the audit date and revision. Inspect plans, conduct, tickets, journal, code, commands and the existing roadmap as local evidence.

## Admission

For each plan assess identifiable evidence, regardless of equivalent organization: dated and revision-anchored status; release fit, upstream and downstream needs and shared budgets; evidenced current state; applicable departures from prior design; target design and file and contract owners; measured goal; phases with entry conditions and observable exits; ticket-sized units with kind, priority, prerequisites and a discriminating check; risks and open decisions. For missing evidence, ambiguous ownership, unretired prerequisite or contradiction, identify the plan section, affected work and precise repair or decision. Keep blocked proposals out of ready rows without excluding unrelated qualified work. Report when no plan qualifies.

## Synthesis and shape

Use the host's actual release names, tests and executable commands. Include a revision-anchored status and these sections: (1) release plan with theme, start and ship summary, (2–4) evidence-backed duplication, gaps and drift, (5) shared files and budgets, (6) decisions and rationale including unresolved decisions, (7) plan-shape guidance, (8) master table and gates, and (9) upkeep. Reconcile a duplicate deliverable to one canonical owner; trace each row to a source plan section. Record conditional release triggers. Distinguish prerequisites requiring merged code in Depends on from ordering alone in Runs before. Explicitly identify every ship clause without executable evidence; do not invent a command.

For each release, section 1 must contain a row whose first cell is exactly bold release name, for example `| **1.2.0** | theme | start | ship |`. Under section 8 use `### 1.2.0` headings and exactly these eight columns, numbered uniquely across releases. Stems must be backticked and unique across rows, tickets and journal. Owner's first word must uniquely match a word in one `docs/*-plan.md` filename, or be `roadmap` for the roadmap itself. Cite the plan section and discriminating outcome in Content. Example (illustrative only; derive actual argv from the host):

| # | Stem | Owner | Kind | P | Depends on | Runs before | Content |
|---|---|---|---|---|---|---|---|
| 1 | `shared-base` | alpha plan | feature | P1 | | | alpha plan phase 1: shared prerequisite; check its result. |
| 2 | `use-base` | beta plan | feature | P1 | `shared-base` | | beta plan phase 2: consume the prerequisite; check the output. |

Write at most one fenced `gate` block per release, with one host-root argv command per line, shell-quoted where needed; put acceptance last. A conditional start uses one `start` block under the release heading in the same argv format. Example:

```gate
clutch roadmap merged --release 1.2.0
clutch roadmap accept 1.2.0
```

## Maintenance

Reconcile the latest file and current ticket and journal identities immediately before an authorized write; report intervening changes. Preserve existing row numbers, stems, authored links, merged strikes, decisions, conditional gates, release history and unrelated text. Assign new work unused numbers and fresh stems; preserve its dependency and release slot. Update shared budgets and files when affected, audit duplication, gaps and drift before releases, remove fixed audit findings and mark recurrences. If the evidence and file already agree, request no edit.
