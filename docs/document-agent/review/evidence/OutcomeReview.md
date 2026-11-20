<!-- clutch:meta
schema: clutch.meta/1.0
kind: plan
purpose: What this tests and why
relates: [docs/document-agent/review/CutReview.md]
owner: docs/document-agent/review/CutReview.md
verified: d7719818
hash: 4e90d27fd117c15338078e52a509c4801efe7320ab8a11cb3d41f8b98c16b2d2
-->
# What this tests and why

A design document that survives every reading-and-writing review can still fail the only test that counts: being built. BuildItReview measures self-containment under writing, CutReview measures scope under skepticism, KillReview measures viability under attack -- all against the TEXT. This review measures the text against REALITY: it compares local evidence from N runs seeded from generations of the same plan, extracts what each run actually paid for (interventions, churn, stalls) and what it got (merges, phases exited, subsystems exercised), and converts the comparison into plan edits. Convergence is the signal, as in the document reviews, but here it is empirical: a failure mode independently exhibited by k of N runs is STRUCTURAL -- a property of the plan or method -- while a failure mode in one run is incidental until a second run reproduces it. The review's second product is the EVIDENCE OVERLAY: a rule for reconciling document-only findings (a CutReview synthesis) with run evidence, because the two can disagree and one of them is data. Designed to re-run whenever a new run finishes or stalls; two runs are enough to start, and each additional run sharpens every convergence count.

# Run shape

Use evidence files supplied in this checkout. For each run, supply a label, the initial and final plans, dated plan patches with commit identifiers, ticket and attempt records, phase-exit evidence, and the operator’s one-line outcome. For lineage comparisons, include candidate parent revisions as of each fork date. Cite the supplied records. Mark missing evidence and leave conclusions that depend on it unresolved.

- N OUTCOME agents, one per run, each isolated to its own evidence. Each confirms, refutes, or qualifies the operator’s characterization from those records.
- 1 LINEAGE agent compares headings and adjacent plan generations, counts sections repeatedly fixed within three or more generations, and tracks changes to the refusals list.
- The orchestrator compares each initial plan with candidate parent revisions as of the fork date. The smallest diff indicates the likely parent. Check whether the child repeated fixes made after the fork. Record ambiguous ancestry when the snapshots do not distinguish the candidates.
- A full CutReview (3 isolated cut agents + 1 synthesis, using [CutReview.md](../CutReview.md)) on the chosen BASE plan -- the generation the outcome evidence says to build from.
- 1 EVIDENCE-OVERLAY pass (orchestrator or a dedicated agent): every synthesis cluster gets a run-evidence verdict before any disposition is adopted (rules below).
- All agents read only their assigned evidence. Reports persist to a review directory as they land (agent output is transient; the disk copy is the record).

# Outcome agent prompt (skeleton, parameterized)

Analyze the supplied local evidence for <RUN_LABEL>, one of <N> seed-plan experiments. Test the operator’s characterization, <ONE_LINE_OUTCOME>, against the artifacts. Use commit messages and changes to distinguish automated work from operator intervention; shared author names cannot establish who acted. Cite uncertainty where attribution is unclear.

Produce an evidence-based report, citing file paths / ticket identifiers / commit shas for every substantive claim, preferring aggregation (grep counts, log stats) over reading everything, deep-reading only the highest-churn items:

1. COMPLETION STATE -- which plan phases were reached and EXITED (exit artifacts read, not claimed); how the run actually ended.
2. TICKET/WORK ECONOMY -- totals, status distribution, attempts per unit, the top-10 churn items and what each churned on.
3. HUMAN INTERVENTION FOOTPRINT -- plan-edit cadence over time; hand edits to code/tickets outside the pipeline; state surgery; burst clusters and what each burst was fighting.
4. DRIFT EVIDENCE -- where practice diverged from the plan-is-seed discipline, in either polarity: code fixed ahead of the plan, or the discipline blocking a needed fix.
5. WHAT AUTOMATED WELL -- quantified (share of merges needing zero touch, one-attempt rate).
6. WHAT STALLED -- recurring failure patterns with named examples and their artifact evidence.
7. PLAN-SECTION SCORECARD -- sections fully built AND exercised / built but never fired / never built.

# Evidence-overlay rules (the reconciliation step)

Stamp every document-review cluster with one verdict before adopting its disposition:

- CONFIRMED -- run evidence independently shows the cost the cut finding predicts (machinery built expensively and never fired; the deferred item's absence never hurt). Adopt, and cite the run evidence as the observed incident.
- UNCONTRADICTED -- no run exercised the question. Adopt on document logic alone; low stakes by construction.
- WEAKENED -- the feature's cost was real but small, or its benefit landed cheaply in some run. Owner's call; prefer the middle disposition (annex, non-blocking, shrink-not-cut).
- CONTRADICTED -- the run evidence shows the opposite: the "unjustified" feature is part of the only configuration that succeeded, or the cut would change a variable correlated with success. REJECT the cluster regardless of its convergence count, and record the rejected experiment in the plan's open-decisions section with its falsification condition -- document logic proposes, evidence disposes.
- One asymmetry is deliberate: a 1/3 (low-convergence) document finding CAN be adopted when run evidence strongly confirms it, exactly as a 3/3 finding can be rejected when evidence contradicts it. Convergence ranks attention; evidence decides.

Findings that appear in the OUTCOME reports but in no document review become the anti-drift edits: each names the runs that paid for its absence (the incident citations), the plan section that owns the fix, and the specific mechanism. Rank by cross-run convergence count, k/N.

# Disposition of results

Everything lands as plan edits to a fresh copy of the base plan, applied in one pass: anti-drift additions (evidence-cited), document-review trims (evidence-stamped), carry-forwards from sibling runs' verified fixes (each proven on a running main), structural edits (exit criteria naming their emitters; deferral lists with named triggers), and an open-decisions section holding every rejected-or-unproven experiment with its closing condition -- so the next run does not silently re-test it. After the edits: re-run CutReview on the revised document, re-run BuildItReview scoped to the earliest unbuilt phases, then seed. The revised plan's success metrics are the parent's observed numbers (in-run plan fixes; per-ticket operator touches); a child run that does not beat both is itself the next OutcomeReview's subject, examined the way the failed forks were. Nothing from this exercise commits code to any analyzed repo.
