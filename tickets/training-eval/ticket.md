---
state: confirmed
source: box:roadmap_row
priority: P3
kind: feature
agent_tier: medium
agent_effort: medium
---

## Depends on
- training-export

## Context
- clutch/training.py
- clutch/llm.py
- docs/training-data-plan.md
- tests/unit/test_main_training_group.py

## On-demand
- clutch/__main__.py
- clutch/docs/host-training.md
- clutch/docs/host-running.md

## Goal / Why
Roadmap row 60 (decision 11). After this ticket `clutch training eval --route <tier>/review --holdout FILE` replays the held-out stems' review records through the given route and prints an agreement score. A host then has a measured number before routing the review surface to its own model, instead of a guess.

Definitions this ticket fixes:
- Held-out records: the stems listed in the file written by `clutch training export --holdout PCT` (one stem per line). Export leaves those stems out of its JSONL, so eval builds their `review` records itself with the same `render` path, selecting only the listed stems.
- Route: `<tier>/<surface>` with tier in `low|medium|high|max`. Only surface `review` is accepted in this ticket. Triage, requisition and implement lenses are a follow-up row filed in Scope in.
- Agreement: each record's recorded label is `negative` (snagged on logic, acceptance, scope or leak) or `neutral`. The route's reply is JSON with a `verdict` of `approve`, `snag` or `rma` (`clutch/specs/review.md`). The record agrees when `verdict == "snag"` exactly when the label is `negative`. A reply that is not JSON with one of those verdicts counts as `unparsed`, never as agreement.
- The report goes to stdout only. Eval calls the LLM seam directly and writes nothing to the journal, the evidence store or the engine log.

## Boundary contract
### Training eval scoring
- disposition: create
- owner: clutch/training.py
- consumers: the `training eval` CLI handler in clutch/__main__.py
- observable change: new `evaluate` and `report_eval` functions in clutch/training.py; `evaluate(records, llm, tier)` returns counts `total`, `agree`, `disagree`, `unparsed` and the agreement fraction
- compatibility: `render`, `report` and `training export` are unchanged except for one new optional keyword `only` on `render`
- acceptance: counts are exact on a scripted FakeLLM; unparseable replies are counted as `unparsed`, not as agree
- tests: tests/unit/test_training_eval.py
- post-merge source of truth: clutch/training.py
- closest existing: `training.render` and `training.report`, which build and summarise export records but never call a model
- earning reason: scoring needs an LLM call and a verdict comparison, which export deliberately does not have; it lives beside `render` because it consumes the same record shape

### Training CLI verb
- disposition: extend
- owner: clutch/__main__.py (`training` group)
- consumers: operators and the shipped host guides
- observable change: new `clutch training eval --route TIER/review --holdout FILE`; exit 0 with the report printed, exit 2 when `training_data.enabled` is false, the route is malformed, or the holdout file is unreadable
- compatibility: `training export` arguments and output are unchanged
- acceptance: parser accepts the new verb and rejects a bad route
- tests: tests/unit/test_training_eval.py and tests/unit/test_main_training_group.py
- post-merge source of truth: clutch/__main__.py

### Export render selection
- disposition: extend
- owner: clutch/training.py::render
- consumers: `training export` (passes nothing) and `training eval` (passes the held-out stems)
- observable change: optional keyword `only` (a set of stems or None); when given, only those stems are rendered and the holdout percentage is ignored
- compatibility: with `only=None` the output and counts are byte-identical to today
- acceptance: a render with `only` returns records for exactly the listed stems; without it, existing export tests still pass
- tests: tests/unit/test_training_eval.py plus the existing export tests
- post-merge source of truth: clutch/training.py

## Scope in / Scope out
Scope in:
- `clutch/training.py`: add `only` to `render`; add `evaluate` and `report_eval`. `evaluate` calls `llm.call(LLMRequest(surface="review", rendered=<record prompt>, tier=tier, effort="medium", ticket=None, worktree=None))` once per record and compares the verdict as defined in Goal.
- `clutch/__main__.py`: add the `eval` subcommand to the `training` group through `_command` with does, reads, writes, lock, exits and an example; add `handle_training` branch that requires `training_data` enabled, reads the holdout file, renders with `only`, builds the LLM the way the other model-calling verbs do (`_preflighted_llm` inside a provider session that is closed afterwards), and prints `report_eval`. Update the group description and help line so they no longer say export only.
- `tests/unit/test_main_training_group.py`: add the new verb to any assertion that lists the group's subcommands.
- Docs follow commands: add a `training eval` row to the verb table in `clutch/docs/host-running.md`, a short section in `clutch/docs/host-training.md` naming the verb, the agreement definition and that only the review lens exists, and update the `training` verb row in `docs/how-clutch-works.md` section 2 if it lists the group's verbs.
- File a follow-up roadmap row for the triage, requisition and implement lenses by running `clutch box suggest` after merge; nothing in this diff covers them.

Scope out: other lenses, any journal or evidence write, training or tuning of a model, changes to export output, spec files.

## Scope fence
- clutch/training.py
- clutch/__main__.py
- clutch/docs/host-training.md
- clutch/docs/host-running.md
- docs/how-clutch-works.md
- tests/unit/test_training_eval.py
- tests/unit/test_main_training_group.py

## Acceptance criteria
1. `./dev.py test tests/unit/test_training_eval.py` passes a case with a scripted `FakeLLM` and three records (negative labelled, replies `snag`; neutral labelled, replies `approve`; negative labelled, replies `approve`): `evaluate` returns `agree == 2`, `disagree == 1`, `unparsed == 0`, not a score of 3 or 0.
2. `./dev.py test tests/unit/test_training_eval.py` passes a case where the reply is `not json` and a case where the verdict is `"maybe"`: both count as `unparsed == 1` and `agree == 0`, never as agreement.
3. `./dev.py test tests/unit/test_training_eval.py` passes a case where `render(..., only={"a"})` returns only stem `a` records while stem `b` records exist, and `render` without `only` returns both.
4. `./dev.py test tests/unit/test_training_eval.py` passes a case with zero records: `report_eval` prints a total of 0 and does not divide by zero.
5. `./dev.py test tests/unit/test_main_training_group.py` passes: `parse_args(["training", "eval", "--route", "medium/review", "--holdout", "h.txt"])` yields the route and holdout path, while `--route medium/triage` and `--route review` are rejected by the parser.
6. `./dev.py test tests/unit/test_training_eval.py` passes a case through the handler with `training_data.enabled` false: the verb refuses with exit 2 and the `FakeLLM` records zero requests.
7. `./dev.py test tests/unit/test_training_eval.py` passes a case asserting the journal file and evidence directory are byte-identical before and after an eval run.
8. `./dev.py test tests/unit/test_training_export.py tests/unit/test_training_export_kinds.py` still passes unchanged, proving `render` without `only` is not altered.
9. `./dev.py test tests/unit/test_main_help.py tests/unit/test_docs_verb.py tests/unit/test_host_running.py` passes with the new verb's help and the new doc rows present.

## Verification
```
./dev.py test tests/unit/test_training_eval.py tests/unit/test_main_training_group.py tests/unit/test_training_export.py tests/unit/test_training_export_kinds.py tests/unit/test_main_help.py tests/unit/test_docs_verb.py tests/unit/test_host_running.py
```

## Definition of rejected
The branch is rejected if eval writes to the journal or evidence store, counts an unparseable reply as agreement, accepts a surface other than `review`, changes `training export` output, or adds a speculative flag beyond `--route` and `--holdout`.

## Time budget
- expected: 20m
- stuck: 40m
