# Review: snag

The dashboard rewrite meets nearly all criteria, but the Stats test never checks the tooltips or the `.stats-row` class that acceptance criterion 7 requires.

## Findings

- [acceptance] tests/mcp_app_dashboard.js:44 Acceptance criterion 7 requires the harness to assert that Stats renders formatted `.stats-row` nodes from `result.tree`, including nested child rows and tooltips. This line only finds the text 'Passed' and '7' and checks that no `<pre>` exists. It never checks that the rows have class `stats-row`. It also never checks that the fake tree's tooltip ('health tip') reaches a `title`, so dropping tooltips or rendering untagged spans would still pass. (do instead: In the Stats section, assert that `.stats-row` nodes exist (`n.className === 'stats-row'`) and that the nested child row sits inside a parent `.stats-row` `<details>`. Also assert that the summary or row carrying 'Health' has `title === 'health tip'`.)

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "6b1f5125449e3850281f4712cf20c0da88018a73",
  "stem": "mcp-dashboard-vscode-parity",
  "reviewed_sha": "6b1f5125449e3850281f4712cf20c0da88018a73",
  "summary": "The dashboard rewrite meets nearly all criteria, but the Stats test never checks the tooltips or the `.stats-row` class that acceptance criterion 7 requires.",
  "findings": [
    {
      "code": "acceptance",
      "path": "tests/mcp_app_dashboard.js",
      "line": 44,
      "message": "Acceptance criterion 7 requires the harness to assert that Stats renders formatted `.stats-row` nodes from `result.tree`, including nested child rows and tooltips. This line only finds the text 'Passed' and '7' and checks that no `<pre>` exists. It never checks that the rows have class `stats-row`. It also never checks that the fake tree's tooltip ('health tip') reaches a `title`, so dropping tooltips or rendering untagged spans would still pass.",
      "paved_road": "In the Stats section, assert that `.stats-row` nodes exist (`n.className === 'stats-row'`) and that the nested child row sits inside a parent `.stats-row` `<details>`. Also assert that the summary or row carrying 'Health' has `title === 'health tip'`.",
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
