# Review: snag

The review panel wiring, combining, cost sum and panel_facts logging are correct and stay within the fence, but the tests check criterion 1 only partly: they never compare the whole returned StageResult, and they check the effect key only when no panel is set, not with `panel: {size: 1}`.

## Findings

- [acceptance] tests/unit/test_review_panel_use.py:81 Criterion 1 requires that the returned StageResult equals the expected one, for both the unset panel and `panel: {size: 1}`. test_single only checks `outcome`, `findings` and the artifact's type. It never compares the whole StageResult, including cost and the artifact's value, against a hand-written expected StageResult. (do instead: Assert `actual == StageResult("gate_failed", <expected SnagList>, [finding()], <expected cost>)` in test_single for both parametrized cases.)
- [acceptance] tests/unit/test_review_panel_use.py:241 Criterion 1 says the effect key `llm/<stem>/<seq>/review/<attempt>/1`, with no `m<k>` scope, must also hold with `panel: {size: 1, combine: findings-union}`. test_single_effect_key runs only with `route.panel` unset, so nothing checks the effect key when a size-1 panel is configured. (do instead: Parametrize test_single_effect_key over unset and `panel(route, 1)`, and assert the same single `llm/item/0/review/1/1` effect key in both cases.)

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "18681be6db1341d2457478919c9a7656afb6c304",
  "stem": "review-panel-stage-use",
  "reviewed_sha": "18681be6db1341d2457478919c9a7656afb6c304",
  "summary": "The review panel wiring, combining, cost sum and panel_facts logging are correct and stay within the fence, but the tests check criterion 1 only partly: they never compare the whole returned StageResult, and they check the effect key only when no panel is set, not with `panel: {size: 1}`.",
  "findings": [
    {
      "code": "acceptance",
      "path": "tests/unit/test_review_panel_use.py",
      "line": 81,
      "message": "Criterion 1 requires that the returned StageResult equals the expected one, for both the unset panel and `panel: {size: 1}`. test_single only checks `outcome`, `findings` and the artifact's type. It never compares the whole StageResult, including cost and the artifact's value, against a hand-written expected StageResult.",
      "paved_road": "Assert `actual == StageResult(\"gate_failed\", <expected SnagList>, [finding()], <expected cost>)` in test_single for both parametrized cases.",
      "kind": null,
      "unit": null
    },
    {
      "code": "acceptance",
      "path": "tests/unit/test_review_panel_use.py",
      "line": 241,
      "message": "Criterion 1 says the effect key `llm/<stem>/<seq>/review/<attempt>/1`, with no `m<k>` scope, must also hold with `panel: {size: 1, combine: findings-union}`. test_single_effect_key runs only with `route.panel` unset, so nothing checks the effect key when a size-1 panel is configured.",
      "paved_road": "Parametrize test_single_effect_key over unset and `panel(route, 1)`, and assert the same single `llm/item/0/review/1/1` effect key in both cases.",
      "kind": null,
      "unit": null
    }
  ],
  "spec_version": "1.9",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "snag"
}
```
