# Review: snag

Mostly correct and within scope, but `evaluate` parses the reply with raw `json.loads`, so it counts a fenced JSON reply as unparsed even though the review spec allows that format and the engine's canonical parser accepts it.

## Findings

- [logic] clutch/training.py:294 `verdict = json.loads(result.text)["verdict"]` parses the raw reply text. The review spec's output contract allows the reply to start with "one json code fence". The engine's canonical reply parser, `clutch/driver.py::unwrap_fence`, strips that fence or pulls a single object out of surrounding prose before it decodes. Eval does neither, so a review route that answers correctly in a fenced `json` block is counted as `unparsed` instead of agree/disagree. That makes the reported agreement too low for exactly the routes the operator is trying to measure, and it adds a second, stricter reply parser next to the existing canonical one. (do instead: Decode `json.loads(unwrap_fence(result.text))` using `clutch.driver.unwrap_fence`, the same path the Review stage uses. Keep the closed verdict check. Add a test case where the reply is a ```json fenced `{"verdict":"snag"}` and a negative label counts as agree.)

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "e7af57a2315da1dcdade078b20f3feba8d5baeda",
  "stem": "training-eval",
  "reviewed_sha": "e7af57a2315da1dcdade078b20f3feba8d5baeda",
  "summary": "Mostly correct and within scope, but `evaluate` parses the reply with raw `json.loads`, so it counts a fenced JSON reply as unparsed even though the review spec allows that format and the engine's canonical parser accepts it.",
  "findings": [
    {
      "code": "logic",
      "path": "clutch/training.py",
      "line": 294,
      "message": "`verdict = json.loads(result.text)[\"verdict\"]` parses the raw reply text. The review spec's output contract allows the reply to start with \"one json code fence\". The engine's canonical reply parser, `clutch/driver.py::unwrap_fence`, strips that fence or pulls a single object out of surrounding prose before it decodes. Eval does neither, so a review route that answers correctly in a fenced `json` block is counted as `unparsed` instead of agree/disagree. That makes the reported agreement too low for exactly the routes the operator is trying to measure, and it adds a second, stricter reply parser next to the existing canonical one.",
      "paved_road": "Decode `json.loads(unwrap_fence(result.text))` using `clutch.driver.unwrap_fence`, the same path the Review stage uses. Keep the closed verdict check. Add a test case where the reply is a ```json fenced `{\"verdict\":\"snag\"}` and a negative label counts as agree.",
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
