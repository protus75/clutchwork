# Review: snag

The fill and Check changes do what the ticket asks, but the integration test header still says it fills a drifted purpose, and the unit test diff deletes the clean-rerun assertions, which hides that a second Check now commits a rewritten owner and relates for the preserved file.

## Findings

- [acceptance] tests/integration/test_check_meta_fill_stage.py:7 Scope in requires rewording this file's `# purpose:` header line, which says it fills a drifted metadata purpose, to say it fills an empty purpose. The diff changes the fixture to `purpose=""` and refreshes `verified`/`hash`, but line 4 still reads 'Check stage fills a drifted metadata purpose through a scripted model call...'. (do instead: Change the line 4 `# purpose:` text to say Check fills an empty metadata purpose through a scripted model call and commits the rewrite as a clutch(<stem>): meta commit, then let Check refresh the hash.)
- [logic] tests/unit/test_check_meta_fill.py:54 The diff deletes the existing 'A clean diff must not ask the model again' block (second `check_meta` call asserting no model factory call and no commit). With the new fixture (`owner=""`, stale `relates`), a second Check finds `docs/old.md` no longer drifted. That sends it through generic `meta.refresh`, which rewrites owner to `engine` and drops the stale relation, so the rerun commits. Deleting the assertion hides this break instead of keeping the existing no-model, no-commit-on-clean-diff coverage. (do instead: Keep the original clean-rerun assertions (`factory.assert_not_called()` and no commit) in a test whose fixture does not depend on preserved empty owner or stale relates. Put the empty-owner and stale-relates preservation check in its own test function so the clean-rerun guard is not removed.)

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "759fd65f22197e15d80eace616bc9644cfcef1d6",
  "stem": "meta-fill-drifted-no-model",
  "reviewed_sha": "759fd65f22197e15d80eace616bc9644cfcef1d6",
  "summary": "The fill and Check changes do what the ticket asks, but the integration test header still says it fills a drifted purpose, and the unit test diff deletes the clean-rerun assertions, which hides that a second Check now commits a rewritten owner and relates for the preserved file.",
  "findings": [
    {
      "code": "acceptance",
      "path": "tests/integration/test_check_meta_fill_stage.py",
      "line": 7,
      "message": "Scope in requires rewording this file's `# purpose:` header line, which says it fills a drifted metadata purpose, to say it fills an empty purpose. The diff changes the fixture to `purpose=\"\"` and refreshes `verified`/`hash`, but line 4 still reads 'Check stage fills a drifted metadata purpose through a scripted model call...'.",
      "paved_road": "Change the line 4 `# purpose:` text to say Check fills an empty metadata purpose through a scripted model call and commits the rewrite as a clutch(<stem>): meta commit, then let Check refresh the hash.",
      "kind": null,
      "unit": null
    },
    {
      "code": "logic",
      "path": "tests/unit/test_check_meta_fill.py",
      "line": 54,
      "message": "The diff deletes the existing 'A clean diff must not ask the model again' block (second `check_meta` call asserting no model factory call and no commit). With the new fixture (`owner=\"\"`, stale `relates`), a second Check finds `docs/old.md` no longer drifted. That sends it through generic `meta.refresh`, which rewrites owner to `engine` and drops the stale relation, so the rerun commits. Deleting the assertion hides this break instead of keeping the existing no-model, no-commit-on-clean-diff coverage.",
      "paved_road": "Keep the original clean-rerun assertions (`factory.assert_not_called()` and no commit) in a test whose fixture does not depend on preserved empty owner or stale relates. Put the empty-owner and stale-relates preservation check in its own test function so the clean-rerun guard is not removed.",
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
