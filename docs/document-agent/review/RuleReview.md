# What this tests and why
AI rule files (`CLAUDE.md`, `AGENTS.md`, and nested rule files) are injected into every session context. As rules accrete, context grows, attention dilutes, and overused hard flags lose force. This review audits the AI rule file at <RULE_PATH> (and any paired rule files at <PEER_PATHS>) for context budget, flag discipline, gate redundancy, discoverability, cross-file alignment, and scoping.

Two invariants frame the review:
* **Document class separation:** The file's annotation (`clutch:meta`) identifies it as either an AI rule or a Spec/Contract. A single document must not mix AI rules with specification/contract prose.
* **Context budget:** A root AI rule file targets **< 200 lines** and **< 8 KB (8,192 bytes)**.

Independent replication separates real bloat and drift from one reviewer's taste: a finding reached by two or more isolated reviewers is real, a single-reviewer finding is a lead. Designed to re-run as rules evolve; on a lean, aligned rule file, few findings is a valid outcome, not a failed review.

# Run shape
* **Mechanical pre-check** (no model): record line count and byte size of `<RULE_PATH>` (and each file in `<PEER_PATHS>`) against the `< 200 lines` / `< 8,192 bytes` budget, inspect `clutch:meta` annotation fields (`kind`, `purpose`, `relates`, `owner`), and identify verbatim-protected extraction-marker regions (e.g., `<!-- clutch:core begin -->` / `<!-- clutch:core end -->`). Pass these results to all agents as facts.
* **3 RULE REVIEW agents**, identical prompt (below), fully isolated: each gets `<RULE_PATH>`, any `<PEER_PATHS>` (such as the paired `CLAUDE.md` / `AGENTS.md` and nested rule files), the mechanical pre-check facts, and any supplied gate/annotation inventory -- no conversation history, no prior review results, no knowledge that other agents exist. Identical prompts keep the convergence statistic clean; withholding prior rounds prevents anchoring on old findings.
* **1 SYNTHESIS agent** (prompt below) merges and verifies the three reports after all finish.
* High reasoning effort for all four. No file writes by any agent; output returns as structured data.

# Rule review agent prompt (verbatim)
You are auditing the AI rule file at <RULE_PATH> (with paired/nested rule files at <PEER_PATHS>, if supplied) to keep always-loaded agent context lean, high-signal, and aligned. Assume every line must earn its token cost until the text proves otherwise. Your only inputs are the supplied rule files and mechanical pre-check facts: no conversation history, no prior reviews, no questions.

Lead with a verdict, no preamble:
* Health: `LEAN` / `TRIMMABLE` / `BLOATED-OR-DRIFTED`.
  * `LEAN`: within `< 200 lines` and `< 8,192 bytes`, properly annotated as an AI rule with no mixed Spec/Contract sections, disciplined `MUST`/`NEVER` flagging, and aligned with paired rule files.
  * `TRIMMABLE`: actionable cuts, compressions, flag adjustments, or subsystem relocations exist, but no structural class-mixing or severe drift.
  * `BLOATED-OR-DRIFTED`: over budget (`>= 200 lines` or `>= 8,192 bytes`), mixed AI-rule and Spec/Contract content, widespread `MUST`/`NEVER` flag inflation, or substantive drift between `CLAUDE.md` and `AGENTS.md`.
* Budget summary: current lines and bytes vs. `< 200 lines` and `< 8,192 bytes`, plus estimated lines/bytes saved if your findings are applied.

Then evaluate `<RULE_PATH>` across these seven checks:

1. **Document class & annotation:**
   * Check whether the file's annotation identifies it as an AI rule (not a Spec/Contract).
   * Flag any passages that are Spec/Contract material (wire schemas, protocol contracts, data models, `MUST`/`SHOULD`/`MAY` specification prose) mixed into the rule file. Propose splitting them into a Spec/Contract document.

2. **Context budget (`< 200 lines`, `< 8,192 bytes`):**
   * Identify the largest sections and single-line paragraphs driving byte/line count.
   * Note verbose phrasing or multi-sentence rationales that can be tightened without losing the rule or its failure history.

3. **Force rating & `MUST`/`NEVER` flag discipline (`0.0`--`1.0` scale):**
   * Rate every behavioral rule in `<RULE_PATH>` on a `0.0` to `1.0` scale, where **`0.0` = absolute prohibition (`NEVER`)**, **`0.5` = neutral preference/default**, and **`1.0` = absolute requirement (`MUST`)**.
   * Produce a **ranked table** ordered from the extremes (`0.0` and `1.0`) inward toward `0.5`, citing line number/heading, short rule name, numeric rating, current flag status, and recommended flag status.
   * Recommend an explicit **flag cutline**: which top-extreme rules earn a `MUST` or `NEVER` flag (sparingly, so flags retain weight) and which rules should be left **unflagged** as plain imperatives or defaults.
   * Flag any bare `SHOULD` lacking an override condition ("Prefer X; use Y when Z") and any `MAY` that does not carve out an exception to a nearby prohibition.

4. **Gate-covered rules:**
   * Identify behavioral rules that are already enforced by a test, linter, hook, or engine gate (as stated in the file or supplied gate inventory).
   * For each, recommend **compress to one line** (naming the gate) or **drop** entirely.

5. **Discoverable facts (code and Annotation system):**
   * Identify architecture descriptions, directory layouts, command/module inventories, or conventions an agent can read directly from the codebase **or** discover from the Annotation system (`clutch:meta` headers -- `kind`, `purpose`, `relates`, `owner` -- and `clutch context suggest`).
   * For each, recommend **drop** or **replace with a one-line routing hint**.

6. **Duplicates & drift (`CLAUDE.md` / `AGENTS.md` / nested rules):**
   * Flag overlapping or contradictory rules within `<RULE_PATH>` and across `<PEER_PATHS>`.
   * `CLAUDE.md` and `AGENTS.md` must stay aligned and as near-identical as possible, differing **only** in how the providers operate or use provider-specific keywords. Flag every substantive divergence, missing rule, or contradictory wording between them.

7. **Subsystem-only rules:**
   * Identify high-detail rules loaded on every session that apply only to a single directory, subsystem, or narrow task type.
   * Recommend relocating each to a nested rule file (e.g., `<subdir>/AGENTS.md`), path-scoped rule, skill, or a crisp lazy pointer-on-demand (*"Before editing X, read Y"*). Never recommend eager `@import` as a context-saving measure -- eager imports expand inline at session start and save zero tokens.

Every finding:
* cites a line number or heading (and peer file location for drift findings) -- no finding without a location;
* states the concrete context cost (bytes/lines) or failure risk;
* respects verbatim-protected extraction-marker blocks (e.g., `<!-- clutch:core begin -->` / `<!-- clutch:core end -->`): if a finding lands inside a managed block, mark it `UPSTREAM-TEMPLATE` rather than proposing a local hand-edit;
* proposes ONE disposition: `flag-must`, `flag-never`, `unflag`, `compress-1-line`, `drop`, `move-nested`, `move-pointer`, `align-peer`, `split-spec`, or `tighten-prose`, with the specific edit.

Rules:
* Evaluate the file as written. Separate "fact from text/pre-check" from "judgment call" and label each.
* Do not pad: a justified, lean rule is not a finding.
* Never recommend dropping a rule solely to hit the byte budget without naming what breaks if the rule is removed.

# Synthesis agent prompt (verbatim)
You receive three rule-review reports produced independently by isolated reviewers from `<RULE_PATH>` (and `<PEER_PATHS>` if supplied), plus the mechanical pre-check facts. Read the file(s), then:
1. **Cluster findings** describing the same rule, section, or drift pair across reports.
2. **Rank clusters:** document-class mixing (`split-spec`) and `CLAUDE.md`/`AGENTS.md` drift (`align-peer`) first; then `3/3` convergence, then `2/3`; within a tier, `drop` / `move-nested` / `move-pointer` > `compress-1-line` > `unflag` / `flag-must` / `flag-never` > `tighten-prose`. Single-reviewer findings labeled judgment call drop; other single-reviewer findings go in a low-confidence tail.
3. **Verify each cluster** against `<RULE_PATH>` (and `<PEER_PATHS>`): drop any finding that misread the text; mark findings inside verbatim-protected extraction markers as `UPSTREAM-TEMPLATE`.
4. **Reconcile the `0.0`--`1.0` force rankings:** for every rule rated by at least two reviewers, report the median rating and spread (`min`--`max`), ranked from extremes (`0.0` and `1.0`) inward toward `0.5`, with the consensus flag cutline (`MUST` / `NEVER` vs. unflagged). Where reviewers disagree on whether a rule earns a flag (spread >= 0.25 or split cutline), surface the disagreement explicitly for the owner rather than averaging it away.
5. **Compute projected budget:** report current lines/bytes and projected lines/bytes if all `3/3` and `2/3` clusters are applied.

Output, verdict first:
* Reconciled verdict (`LEAN` / `TRIMMABLE` / `BLOATED-OR-DRIFTED`) with any verdict disagreement explained.
* Budget table (current vs. projected lines and bytes against `< 200 lines` / `< 8,192 bytes`).
* Ranked force table (`0.0`--`1.0` median/spread, recommended `MUST`/`NEVER` vs. unflagged cutline, and flagged disagreements).
* Ranked finding clusters with convergence counts, dispositions, and `UPSTREAM-TEMPLATE` tags where applicable.
* Low-confidence tail.

# Disposition of results
Findings become reviewed edits to the rule files (or, for `UPSTREAM-TEMPLATE` findings, edits to the owning template); the review re-runs after material edits. The flag cutline and every cut or relocation decision belong to the owner, informed by convergence counts and loss statements -- the review recommends, it does not decide. Nothing from this exercise commits code or edits files automatically.
