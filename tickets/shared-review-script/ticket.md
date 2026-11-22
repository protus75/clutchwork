---
state: draft
source: human
priority: P0
kind: feature
---

## Depends on
- none

## Context
- tests/integration/test_stages.py::implement_reply
- tests/integration/test_stages.py::verdict
- tests/integration/test_requisition.py::reply
- tests/integration/test_requisition_gate.py::reply
- tests/integration/test_author.py::requisition_reply
- tests/integration/test_triage.py::requisition_reply
- tests/integration/test_review_command.py::reply
- tests/integration/test_shared_fakes_adoption.py
- clutch/llm.py::FakeLLM

## Goal / Why
Tests script the exact order of model replies (`FakeLLM` lists), and the per-stage reply shape is copied into six test files. When the engine changes how many requisition-review, review or implement calls happen, or in what order, every copy and every script breaks outside the ticket's fence. After this ticket one module, `tests/stage_replies.py`, owns the JSON shape of a requisition-review reply, a review verdict and an implement report, plus `script(requisition=..., implement=..., review=...)`, which returns the `FakeLLM` list in engine call order (requisition, implement, review). The seven duplicated reply helpers in those six files are gone and import the shared ones. New tests can then script by stage and a call-order change edits one place. Rewriting each existing script's sequence is out of scope.

## Boundary contract
### Stage reply builders
- disposition: create
- owner: tests/stage_replies.py
- consumers: tests/integration/test_stages.py, tests/integration/test_requisition.py, tests/integration/test_requisition_gate.py, tests/integration/test_author.py, tests/integration/test_triage.py, tests/integration/test_review_command.py, and every test that scripts a stage
- observable change: `requisition_reply(verdict, findings=None, dependents=None)`, `review_verdict(verdict="approve", findings=None)`, `implement_reply(outcome="ok", findings=None)` and `script(*, requisition=None, implement=None, review=None)` exist; each migrated file imports them instead of defining its own copy
- compatibility: each builder returns byte-identical text to the helper it replaces for the same arguments; names other test files import from the migrated files (`verdict`, `implement_reply`, `requisition_reply`, `reply`) remain importable from the same modules, so no importer is edited
- acceptance: shape tests validate each builder's output against the production models; a repo-reading test finds no local copy in the migrated files
- tests: tests/unit/test_stage_replies.py, tests/integration/test_shared_stage_replies.py
- post-merge source of truth: tests/stage_replies.py
- closest existing: tests/integration/test_stages.py::verdict and ::implement_reply, tests/integration/test_triage.py::requisition_reply, tests/fakes.py
- earning reason: consolidation of evidenced duplicates (the same requisition-review reply JSON is defined in five test files, the review verdict and implement report in the sixth, imported by about 25 more); tests/fakes.py holds seams, not reply shapes, and importing a helper from another test module is the coupling this removes

### Production code
- disposition: reuse
- owner: clutch/llm.py, clutch/requisition.py, clutch/artifacts.py, clutch/stages.py
- consumers: unchanged
- observable change: none
- compatibility: production code, prompt specs and `tests/approval.py` are not touched
- acceptance: the diff lists no path under `clutch/`
- tests: tests/unit/test_stage_replies.py
- post-merge source of truth: clutch/requisition.py::RequisitionReply

## Scope in / Scope out
In:
- Create `tests/stage_replies.py`. `requisition_reply` returns `json.dumps({"verdict": verdict, "summary": "reviewed", "findings": findings or [], ...})` and adds `"dependents"` only when `dependents` is given; it never validates the verdict, because tests pass `reply("wrong")` to script an invalid reply. `review_verdict` returns the shape `test_stages.py::verdict` returns today (summary `looked`). `implement_reply` returns the fenced-json text `test_stages.py::implement_reply` returns today. `script` returns the list of replies for the stages given, in the order requisition, implement, review, skipping `None`; a `str` value is a verdict or outcome name passed to the matching builder, any other value (callable, `LLMResult`, exception) passes through unchanged.
- Migrate: in `test_stages.py` delete `verdict` and `implement_reply` and import them (`review_verdict as verdict`); in `test_requisition.py` and `test_review_command.py` delete `reply` and import `requisition_reply as reply`; in `test_author.py` and `test_triage.py` delete `requisition_reply` and import it; in `test_requisition_gate.py` keep `reply(verdict, code)` as a thin wrapper that builds its one finding and calls `requisition_reply`. Remove any import (`json`) that becomes unused in a migrated file.
- Create `tests/unit/test_stage_replies.py` and `tests/integration/test_shared_stage_replies.py`.
Out: rewriting existing scripts, `tests/approval.py`, triage/diagnosis/author reply helpers, `tests/harness/`, `tests/integration/test_eval_harness.py` (different finding shape), `tests/integration/test_scorecard.py` inline copy, and all production code. A further sweep is a separate ticket.
The hot files `test_stages.py` and `test_requisition.py`-family edits are forced: each deletes a local definition and adds one import line.

## Scope fence
- tests/stage_replies.py
- tests/unit/test_stage_replies.py
- tests/integration/test_shared_stage_replies.py
- tests/integration/test_stages.py
- tests/integration/test_requisition.py
- tests/integration/test_requisition_gate.py
- tests/integration/test_author.py
- tests/integration/test_triage.py
- tests/integration/test_review_command.py

## Acceptance criteria
1. `requisition_reply("approve")` equals `json.dumps({"verdict": "approve", "summary": "reviewed", "findings": []})`, adds `dependents` only when given, and `RequisitionReply.model_validate_json` accepts `requisition_reply("snag", [finding], [dependent])`; `requisition_reply("wrong")` still returns text, not an exception; checked by `./dev.py test tests/unit/test_stage_replies.py`.
2. `review_verdict("snag", [SNAG])` parses with `ReviewVerdict` and `implement_reply()` parses with `ImplementReply` after stripping its json fence; neither is the empty string; checked by `./dev.py test tests/unit/test_stage_replies.py`.
3. `script(requisition="approve", implement="ok", review="approve")` returns three strings in that order and `script(review="snag")` returns one, not three; a callable passed as `implement` is returned as the same object; checked by `./dev.py test tests/unit/test_stage_replies.py`.
4. The six migrated files define no local copy: none contains `def verdict(`, `def implement_reply(`, `def requisition_reply(`, the text `"summary": "reviewed"` or the text `"predicted_vs_actual"`, except that `test_requisition_gate.py` and `test_requisition.py` may keep `def reply(`, which must call `requisition_reply`, and `test_requisition.py` and `test_review_command.py` contain no `def reply(` at all; checked by `./dev.py test tests/integration/test_shared_stage_replies.py`, which reads the files through a `Path(__file__)` anchor.
5. `tests/stage_replies.py` is the only file under `tests/` besides the files listed as out of scope that contains `"summary": "looked"`; checked by `./dev.py test tests/integration/test_shared_stage_replies.py`.
6. The migrated files and their importers pass unchanged in behavior; checked by `./dev.py test tests/integration/test_stages.py tests/integration/test_requisition.py tests/integration/test_requisition_gate.py tests/integration/test_author.py tests/integration/test_triage.py tests/integration/test_review_command.py tests/integration/test_audit.py tests/integration/test_terminal.py`.
7. The diff changes no path outside the scope fence, so none under `clutch/`; checked by `./dev.py test tests/unit/test_stage_replies.py` for the importability of `tests.stage_replies` without importing any migrated test module.

## Verification
```
./dev.py test tests/unit/test_stage_replies.py tests/integration/test_shared_stage_replies.py tests/integration/test_stages.py tests/integration/test_requisition.py tests/integration/test_requisition_gate.py tests/integration/test_author.py tests/integration/test_triage.py tests/integration/test_review_command.py tests/integration/test_audit.py tests/integration/test_terminal.py
```

## Definition of rejected
A builder whose text differs from the helper it replaces, a migrated file still defining its own copy, a changed script sequence in an existing test, any edit under `clutch/`, or `script` validating or reordering replies beyond the stated order.

## Time budget
- expected: 25m
- stuck: 50m
