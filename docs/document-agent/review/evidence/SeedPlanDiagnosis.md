<!-- clutch:meta
schema: clutch.meta/1.0
kind: plan
purpose: Seed-plan diagnosis — prompt
relates: []
owner: engine
verified: d7719818
hash: cfef366dc6711ac4269fa4e0d08130b9b0a66d3c3f5afeda649e83baf22e1bf5
-->
# Seed-plan diagnosis — prompt

## What this tests and why

Compare two independent builds by different providers that started from the same seed. Use the run evidence supplied in this checkout.

Two goals, in priority order:

1. **PRIMARY — diagnose the seed's gaps.** For each build, work out every plan defect the experiment exposed: what the builder had to invent, what it got wrong and later corrected, what it contradicted, what it could not build in the stated order. Go **deeper than `BuildItReview.md`**: that review measures self-containment for the *earliest unbuilt phases* by dry-run; here you have the *whole* build history of *two* independent runs as evidence, so you can find defects a single dry-run never reaches — ones that only surface once code is written, a phase boundary is crossed, or the two builders diverge on the same passage.
2. **SECONDARY — compare the two providers.** Where the same seed passage produced *different* outcomes, say why: plan-logic reading, ticket authoring, ticket implementation. Convergence is the strongest signal — a defect **both** providers hit is almost certainly a real seed defect, not one model's quirk.

The deliverable is a review report; its findings become edits folded back into a new `SEED_PLAN.md` (the corrected common ancestor). Nothing here commits code to either experiment.

## Evidence — read all of it before diagnosing

**Seed identity.** Compare the supplied initial plan from each run. Normalize only the project name. If the plans differ elsewhere, report the differences before attributing different outcomes to providers.

**Build histories.** For each labeled run, read the local copies of the initial and final plans and the dated sequence of plan edits, including commit messages and patches. Read the message for the defect the builder claimed, then the diff for the fix it actually made.

**Corroboration.** Compare the supplied tickets, implementation excerpts, prior findings, configuration, and provider instructions. Use them to check whether a plan edit resolved the observed failure. Identify missing evidence explicitly and limit the verdict to what the supplied files establish.

**House style** — every finding cites a location, states a concrete failure scenario (what breaks, under what conditions, observed how), separates *fact* ("this is wrong") from *opinion* ("I'd do it differently") and labels each, and ends with a one-sentence edit that resolves it. No finding without a location. No praise unless load-bearing.

## Method

Run three passes; be exhaustive on defects before polishing prose.

**Pass 1 — per-build defect ledger (review each run independently).** Walk each plan's history from seed to head. For every edit that corrects the plan, record one entry:
* **location** — seed section/heading the defect lived in.
* **class** — `missing` (seed silent) / `ambiguous` (two defensible readings) / `contradictory` (two passages disagree) / `wrong-order` (can't build in stated sequence) / `unbuildable` (no edit short of redesign fixes it).
* **evidence** — the commit(s), ticket(s), or review finding that exposed it, cited by hash/path.
* **failure scenario** — what the builder did wrong or had to invent, concretely, before the fix.
* **fix as applied** — what that build changed, and whether the fix looks *correct*, *partial*, or *itself defective* (a bad fix is a finding).

**Pass 2 — cross-provider comparison.** Cluster Pass-1 entries that trace to the **same seed passage** across the two builds:
* **Convergent** (both builders hit it) → high-confidence seed defect. Rank these first.
* **Divergent** (only one hit it, or they fixed it differently) → attribute the difference: was it plan-logic reading, ticket authoring, or ticket implementation? Which provider's outcome is better, and would the *seed* text have forced the better one? Compare observed plan-edit and ticket counts and explain differences the evidence supports.
* **Single-build, no divergence signal** → low-confidence tail.

**Pass 3 — verify before reporting.** For each cluster, re-read the seed: if the seed *actually* determines it and the builder missed it, reclassify as **FINDABILITY** (structure defect — answer exists but wasn't found where a reader looks), not a content gap. Drop anything that turns out to be a build-side mistake with no seed cause.

## Report — write to `SEED_PLAN_DIAGNOSIS.md`

Verdict first, then evidence:

1. **Verdict** per build (`SEED SOUND` / `SEED GAPS — FIXABLE` / `SEED NOT BUILDABLE AS WRITTEN`, with the one defect that grounds a NOT-BUILDABLE named) and one reconciled verdict for the seed.
2. **Ranked seed-defect list.** Convergent (both builds) first, then single-build; within a tier `contradictory > wrong-order > ambiguous > missing`. Each: location, class, convergence count (1/2 or 2/2), failure scenario, and **the exact seed edit** to make — quote the seed line to change and give its replacement, so the edit can be applied to `SEED_PLAN.md` without re-deriving it.
3. **Cross-provider comparison** — the Pass-2 findings: where the same seed text produced different plan logic / tickets / implementations, which provider did better, and whether the seed forced or merely permitted it.
4. **FINDABILITY list** — seed answers that exist but sit where builders didn't look; each with a placement/cross-reference edit.
5. **Low-confidence tail** — single-build findings without a convergence or provider signal.
6. **`SEED_PLAN.md` change set** — the ordered, deduplicated edits from §2 and §4, ready to apply to a fresh copy of the seed. Where the two builds fixed the same defect **differently**, do not stall: pick the better fix, write it as the change, and justify the choice in one or two sentences (why it is more correct, more self-contained, or more consistent with the rest of the seed — not merely which provider you trust). Mark each such entry `CONFLICT — recommended: <run label>` so the owner can see at a glance every place you chose between two fixes and can overrule; the recommendation is yours, the approval is theirs.

The report recommends; the owner approves edits before they land in `SEED_PLAN.md`. Nothing here commits code to either build.
