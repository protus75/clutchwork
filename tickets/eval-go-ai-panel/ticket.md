---
state: confirmed
source: box:roadmap_row
priority: P1
kind: feature
agent_tier: medium
agent_effort: medium
---

## Depends on
none

## Context
- eval/harness.py::_go_report
- eval/harness.py::record_go
- eval/harness.py::_run
- eval/harness.py::main
- eval/harness.py::_author_fixtures
- eval/harness.py::run_author_graph
- eval/harness.py::refuse_same_author
- clutch/artifacts.py::AuthorGraph
- clutch/artifacts.py::ReviewBaselineReport
- tests/integration/test_go_grade.py
- tests/integration/test_eval_harness.py

## Goal / Why
Decision 19 (`docs/roadmap.md`, roadmap row 101) takes GO baselines from an AI panel of a different model family than the judge, so no person has to sign off. Today `eval/harness.py::_go_report` refuses GO unless a person passes `--approve-author-graph`. After this change a model whose provider differs from the review judge's judges the Author graph and returns approve or refuse with a reason. That judgment is stored in the GO report as `graph_panel`. `--approve-author-graph` no longer exists. GO is recorded only when the panel approves.

A "family" here is the config provider, the same unit `tests/unit/test_roadmap_accept.py::test_judge_family` compares. The family check is stricter than `refuse_same_author`, which refuses only an identical (provider, model) pair. The panel is refused when `panel.member.provider` equals the provider of `baseline_identity(config)['review']['rows'][tier]`. The tier is the one `_go_report` already uses for its identity check. A same-provider, different-model panel is therefore refused.

Rejected simpler approach: keeping the flag and only adding a model call beside it. That leaves two authorities for one judgment, and the report would not say which one decided.

## Scope in / Scope out
In `clutch/artifacts.py`:
- Add a closed model `GraphPanel` with `member: AuthorIdentity`, `approve: bool` and `reason: NonBlank`.
- Add the field `graph_panel: GraphPanel | None = None` to `ReviewBaselineReport`. The default keeps every existing report valid.

In `eval/harness.py`:
- `_go_report` and `record_go` drop the `approve_author_graph` parameter. `record_go` takes `panel: GraphPanel | None`.
- `_go_report` keeps its floor and identity checks. It adds a check: `panel` must be present and `panel.approve` must be `True`. It also refuses when `panel.member.provider` equals the review row's provider (looked up through `baseline_identity` as above, not through `refuse_same_author`). Each refusal is a `FixtureError` whose message names the panel; the provider refusal also contains the word "family".
- `record_go` writes the panel into the recorded report's `graph_panel`.
- Add `async judge_author_graph(driver, *, report, member, ...)`. It reuses the `run_author_graph` call shape to ask the pinned panel member to judge `report.author_graph`. It returns a `GraphPanel` built from a closed reply with `approve` and `reason`. A non-`ok` outcome raises `FixtureError`.
- `_run`, when `go_report` is set, validates the report, then calls `judge_author_graph` through a pinned route for the chosen provider (as `_author_fixtures` does), then calls `record_go`.
- `main` replaces `--approve-author-graph` with `--panel-provider NAME` (default `codex`, as `author` does) and `--panel-tier`.
- Update the module docstring usage line that names `--approve-author-graph`.

Out: the review scoring, the signal body, `baseline_identity`, `refuse_same_author`, and the visual baseline. Also out: `docs/roadmap.md` (the roadmap driver stamps its own row) and `CLUTCH_PLAN.md` (frozen).

`tests/integration/test_go_grade.py`: drop the `approve` argument and the `approve=False` case, and add `graph_panel` to the expected closed key set in `test_review_baseline_report_closed_schema`. Its `harness._run(cfg, {}, lambda: None, out=out, go_report=measured)` case (near lines 58-60) currently expects `FixtureError` matching 'judgment' and an unchanged tmp tree. After this change `_run` would reach a real provider, so that case monkeypatches `harness.ProviderLLM` with a FakeLLM whose `preflight` returns `[]` and whose reply is a refusing panel, as `tests/integration/test_eval_harness.py` (around lines 266-289) already does. The case passes env `{'PATH': '/usr/bin:/bin'}` and clock `lambda: NOW`, as `test_eval_harness.py` already does (the git describe step and the lockfile and journal timestamps need a real PATH and a real timestamp). The panel call uses the `--panel-provider` default `codex`, which differs from the test config's review provider `claude`. The tmp tree cannot stay byte-identical on this path, because `_run` takes the lockfile in `config.state_dir` and the driver writes journal events and spools. So the case expects `FixtureError` matching 'panel' plus three things that the refusing path keeps: no SIGNAL event with `verdict == 'GO'` is in the journal, `out` does not exist, and the bytes of the measured report file are unchanged. The repo fixtures are checked as `test_go_grade_existing_corpus_is_partial_no_go` does. No other expectation there changes.

## Scope fence
- eval/harness.py
- clutch/artifacts.py
- tests/integration/test_go_grade.py
- tests/integration/test_go_ai_panel.py
- tests/unit/test_go_panel_schema.py

## Acceptance criteria
1. `tests/integration/test_go_ai_panel.py` checks that `record_go` with `panel=None`, or with a panel where `approve` is `False`, raises `FixtureError` matching "panel". It also checks that the journal is unchanged and the out file is absent, so no GO is written.
2. The same file checks that a panel whose `member.provider` equals the review row's provider raises `FixtureError` matching "family", not a recorded GO. It covers two cases: the identical (provider, model) pair, and the same provider with a different model. Both raise, and neither records GO.
3. The same file checks that an approving panel from a different provider records GO. It checks that `recorded.graph_panel == panel`, that the file written to `out` reloads through `ReviewBaselineReport.model_validate_json` to the same value, and that the journal's last event is the GO signal.
4. The same file checks `judge_author_graph` with a hand-built fake driver (the fake returns a closed reply, because real providers are not called in tests). A reply with `approve=False` returns a panel with `approve is False`, not `None` and not an exception. A fake outcome other than `ok` raises `FixtureError`.
5. The same file checks `harness._run(cfg, {'PATH': '/usr/bin:/bin'}, lambda: NOW, out=out, go_report=path)` end to end with `harness.ProviderLLM` monkeypatched to a FakeLLM and the panel provider `codex` (the config's review provider is `claude`). With a refusing panel reply it raises `FixtureError` matching "panel", no SIGNAL event with `verdict == 'GO'` is in the journal, `out` does not exist, and the bytes of the `go_report` file are unchanged. With an approving reply from a different provider it records GO and the written report has `graph_panel.approve is True`.
6. The same file checks that `harness.main(["run", "--record-go", path, "--approve-author-graph"])` raises `SystemExit` with code 2, because the flag is gone.
7. `tests/unit/test_go_panel_schema.py` checks that `GraphPanel` rejects an extra key, a non-bool `approve` such as `"yes"`, and a blank `reason`. It checks that `ReviewBaselineReport` still validates a report that omits `graph_panel`, with `graph_panel` equal to `None`.
8. `tests/integration/test_go_grade.py` passes, with `record_go` called without `approve_author_graph`, the closed key set including `graph_panel`, and the `_run` case driven by the fake `ProviderLLM`, env `{'PATH': '/usr/bin:/bin'}` and clock `lambda: NOW`.

## Verification
```
./dev.py test tests/integration/test_go_grade.py tests/integration/test_go_ai_panel.py tests/unit/test_go_panel_schema.py tests/integration/test_eval_harness.py
```

## Definition of rejected
Any path that records GO without an approving panel from a provider that differs from the review judge's. A kept `--approve-author-graph` flag or a second approval path. A GO report that does not name the panel member and its reason. A change to review scoring or to the signal body.

## Time budget
- expected: 30m
- stuck: 60m
