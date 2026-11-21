# Review: snag

Both earlier findings are fixed and the fill pipeline is correct, but criterion 5 is only partly met: `tests/unit/test_main_meta_fill.py` never checks that `meta check` and `meta refresh` output stays the same for the same inputs.

## Findings

- [acceptance] tests/unit/test_main_meta_fill.py:13 Criterion 5 requires `tests/unit/test_main_meta_fill.py` to prove that `asyncio.run(_run_meta("fill", ..., ask=fake))` exits 0 or 1, and that `meta check` and `meta refresh` outputs for the same inputs are unchanged. This file only tests the fill exit code and the parser. No test here runs `_run_meta("check", ...)` or `_run_meta("refresh", ...)` against the async `_run_meta` and asserts on their stdout and return values, so the second half of the criterion is unproven in the file the criterion names. (do instead: In tests/unit/test_main_meta_fill.py, add a test that runs `asyncio.run(_run_meta("check", ...))` and `asyncio.run(_run_meta("refresh", ...))` on a MemoryFS input. Assert the exact return codes and captured stdout, for example check prints `docs/a.md: missing` and returns 1, refresh prints the changed path and returns 0, and a later check prints `empty_purpose`. That proves the async signature left both verbs' output unchanged.)

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "f9e953e72e796536fcc5838294cd174c377380a0",
  "stem": "meta-fill-surface",
  "reviewed_sha": "f9e953e72e796536fcc5838294cd174c377380a0",
  "summary": "Both earlier findings are fixed and the fill pipeline is correct, but criterion 5 is only partly met: `tests/unit/test_main_meta_fill.py` never checks that `meta check` and `meta refresh` output stays the same for the same inputs.",
  "findings": [
    {
      "code": "acceptance",
      "path": "tests/unit/test_main_meta_fill.py",
      "line": 13,
      "message": "Criterion 5 requires `tests/unit/test_main_meta_fill.py` to prove that `asyncio.run(_run_meta(\"fill\", ..., ask=fake))` exits 0 or 1, and that `meta check` and `meta refresh` outputs for the same inputs are unchanged. This file only tests the fill exit code and the parser. No test here runs `_run_meta(\"check\", ...)` or `_run_meta(\"refresh\", ...)` against the async `_run_meta` and asserts on their stdout and return values, so the second half of the criterion is unproven in the file the criterion names.",
      "paved_road": "In tests/unit/test_main_meta_fill.py, add a test that runs `asyncio.run(_run_meta(\"check\", ...))` and `asyncio.run(_run_meta(\"refresh\", ...))` on a MemoryFS input. Assert the exact return codes and captured stdout, for example check prints `docs/a.md: missing` and returns 1, refresh prints the changed path and returns 0, and a later check prints `empty_purpose`. That proves the async signature left both verbs' output unchanged.",
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
