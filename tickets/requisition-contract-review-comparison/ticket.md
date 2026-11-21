---
state: draft
source: human
priority: P0
kind: feature
---

## Depends on
- requisition-review-compact-context
- plan-subagents-explicit-sonnet

## Context
- clutch/requisition.py
- clutch/ask.py
- clutch/config.py::Config
- clutch/__main__.py::main
- clutch/training.py::evaluate
- clutch/evidence/schema.py
- eval/diagnose.py
- eval/harness.py
- docs/boundary-contract-plan.md
- clutch/docs/host-training.md
- tests/unit/test_main_help.py
- tests/unit/test_main_training_group.py

## Goal / Why
Measure whether explicit interface/boundary design contracts let a single Sonnet reviewer replace the full buildability review plus independent audit without losing defect detection. Compare against independently labeled fixture truth, not agreement with Opus. The owner's November 21 observation is a hypothesis, not a premise that contracts guarantee correctness: include explicit-but-wrong contracts, contract/implementation mismatches, missing forced callers and missing test obligations. Deliver the bounded comparison and a recommendation; do not silently change the production review policy. This ticket uses the compact production material and explicit Sonnet child policy delivered by its dependencies.

## Boundary contract
### Review comparison operator command
- disposition: extend
- owner: clutch/__main__.py training group
- consumers: owner and bounded evaluation runner
- observable change: add clutch training review-compare --fixtures DIR --out PATH under the existing training group, dispatching to a review-comparison module through existing provider/driver seams
- compatibility: existing training export/eval behavior and their enablement guard are unchanged; dispatch the synthetic comparison before that export/eval guard so it does not require enabling private training capture; no production review route or approval is changed
- acceptance: help states reads, writes, lock, costs, exit codes and examples; the command produces a complete or explicitly inconclusive report with bounded calls and budget
- tests: tests/unit/test_review_compare_cli.py and tests/integration/test_review_compare_cli.py
- post-merge source of truth: clutch/__main__.py training group

### Review comparison report
- disposition: create
- owner: clutch/reviewcompare.py
- closest existing: eval/harness.py scores implemented diffs; clutch/training.py::evaluate replays recorded diff-review labels; neither measures authored-ticket buildability with contract-stratified truth and a separate audit cost.
- earning reason: a persisted evaluation artifact is the process boundary needed to decide whether this owner's costly full-review workflow can be replaced; reuse existing provider invocation and evidence owners instead of creating another model runner.
- consumers: training review-compare command and its independent report verifier
- observable change: a JSON report names corpus/spec/model identities, each arm's verdicts and caught/missed defects, false snags, invalid replies, call counts, cache/uncached/output tokens, reported USD and wall time, with contract-present/legacy strata.
- compatibility: no new journal signal, live ticket verdict, approval cache entry, training record format or production prompt authority.
- acceptance: scores recompute from labeled cases; missing or budget-stopped calls remain inconclusive, never zero-cost success; recommendation retains full review when quality evidence is insufficient.
- tests: tests/unit/test_review_compare.py and tests/integration/test_review_compare_cli.py
- post-merge source of truth: clutch/reviewcompare.py report schema and eval/requisition_compare/ labeled fixtures

## Scope in / Scope out
Scope in:
- Add a narrow grouped operator command and module for this single comparison. The required --fixtures directory is explicit so the installed command never assumes the clutch source repository or reads its tickets implicitly; missing/invalid fixture input refuses before any provider call. Use the existing read-only provider-session pattern, injected clock/process/filesystem seams and existing evidence capture. Keep model call records in evidence but do not journal requisition_verdict or allow evaluation approval to release a real ticket. Model requests run against isolated synthetic fixture repositories through existing Git/workspace wrappers.
- Commit exactly 12 deterministic authored-ticket fixture cases in eval/requisition_compare: three defective and three clean with explicit boundary/interface contracts, and three defective and three clean without explicit interface entries (use a valid Boundary contract none/private-implementation declaration; never omit a required ticket section). Label expected verdict and defect location/reason independently from reviewer output. Include plausible incorrect contracts and wrong/missing caller/test migration. Parse real tickets and run real authoring lint for fixture validity; label buildability defects separately from mechanical lint errors. Labels stay outside model-visible material.
- All model replies use the existing RequisitionReply JSON contract (verdict, summary, dependents, findings). For the audit, reuse the shipped adversarial checks but adapt only its output presentation to this schema; retain its read-only and verified-evidence constraints, and include this adaptation in report provenance. The deterministic scorer counts a defective case as caught only when a blocking verdict includes a finding overlapping the independently labeled path and inclusive line range; an unrelated snag is not a catch. A blocking verdict on a clean case is a false snag. No model judge or synthesis call is added.
- For every case, candidate arm is one explicitly selected Sonnet review with a concise contract-first instruction: check interface obligations, contradictions, forced callers, scope and named verification; perform read-only lookup when needed. Baseline arm is a fresh full production requisition review on Opus plus a separate fresh Sonnet adversarial audit using the shipped review-audit instructions. The baseline combined result rejects when either reviewer finds a real blocker; record both component outputs so extra false snags remain visible. Match input repository/ticket bytes between arms, and do not feed either arm the other's output or expected labels. An independent audit means a separate provider invocation, not an additional agent team or hidden synthesis call.
- Before invocation, bound the run to 36 scored calls and a 20 USD reported-spend stop threshold, with the provider's per-call remaining-budget support and existing timeout seams. Count any preflight probes separately in the report overhead. Pass the remaining budget on every scored invocation, stop starting calls when reported cumulative spend reaches 20 USD, and report any indivisible last-call overshoot rather than claiming a strict token-meter cap. Stop on exhausted budget or provider quota; keep partial output as inconclusive and do not repeatedly retry it to manufacture completeness.
- Report totals and per-stratum caught defects, false snags, invalid replies, calls, token categories, reported cost and elapsed time. Do not interpret raw cached token totals as quota. All three contract-bearing defects must be caught and no contract-bearing clean case falsely snagged before recommending removal of full review on that stratum; this is a bounded pilot, not proof of general safety. Report weaker or inconclusive evidence honestly without requiring the cheaper arm to win for this ticket to complete.
- Run the bounded comparison once through the new clutch verb and commit eval/requisition_compare_report.json plus docs/requisition-review-comparison.md with the actual results, limitations and recommendation. If provider quota prevents completion, commit the actual partial report and a clearly inconclusive recommendation; fake-only scores do not count as the live experiment.
- Add fake-driven unit coverage of scoring, cold/warm token accounting, arm isolation, label withholding, budget stop and recommendation logic, plus CLI/help/composition integration coverage. Extend the training group description and CLI help; update README, training guide, host-running verb table, how-clutch-works command table, and the extension README's training-command description if it lists those verbs. Add extension help only if an extension surface is actually introduced; this command does not add one.
Scope out:
- No automatic policy promotion, new training-data export lens, pricing estimator, model leaderboard framework, provider installation, production ticket mutation, or changes to the document-agent pipeline. The candidate reviewer prompt is evaluation-only; there is one production requisition-review path.


## Scope fence
- clutch/reviewcompare.py
- clutch/__main__.py
- eval/requisition_compare/
- eval/requisition_compare_report.json
- docs/requisition-review-comparison.md
- tests/unit/test_review_compare.py
- tests/unit/test_review_compare_cli.py
- tests/integration/test_review_compare_cli.py
- README.md
- clutch/docs/host-training.md
- clutch/docs/host-running.md
- docs/how-clutch-works.md
- vscode-clutchwork/README.md

## Acceptance criteria
1. `./dev.py test tests/unit/test_review_compare.py tests/unit/test_review_compare_cli.py tests/integration/test_review_compare_cli.py tests/unit/test_main_help.py tests/unit/test_main_training_group.py` proves fixture truth is hidden, the arms are isolated, invalid replies are scored as invalid, and both contract-bearing and legacy strata contribute independent detection/false-snag results.
2. `./dev.py test tests/unit/test_review_compare.py tests/integration/test_review_compare_cli.py` proves capped/failed calls cannot become favorable results, probes and both baseline invocations are counted, cache categories stay separate, and an evaluation never writes production approval signals.
3. `eval/requisition_compare_report.json` and `docs/requisition-review-comparison.md` record the actual bounded live comparison or an actual budget/quota-stopped inconclusive result, with model/spec/corpus identities and a recommendation specifically assessing the interface-contract hypothesis.
4. `./dev.py test tests/unit/test_review_compare.py` recomputes the recommendation: the cheaper contract-bearing arm must catch every planted defect and falsely snag no clean contract-bearing case; missing evidence cannot authorize removal of full review.

## Verification
```
./dev.py test tests/unit/test_review_compare.py tests/unit/test_review_compare_cli.py tests/integration/test_review_compare_cli.py tests/unit/test_main_help.py tests/unit/test_main_training_group.py
```

## Definition of rejected
Removing required checks without evidence, introducing a second production authority, adding speculative settings, or changing files outside the fence.

## Time budget
- expected: 30m
- stuck: 60m
