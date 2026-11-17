# Review: snag

The ten scripts are guarded correctly and the earlier `main` shadowing is fixed with the `clutch_main` alias, but the new test skips the guard-line text check for two of the ten files, so acceptance criterion 3 is only partly met.

## Findings

- [acceptance] tests/integration/test_regress_scripts_guarded.py:18 The test skips the guard-line check for any script whose text contains `from clutch.__main__ import main`. After the alias fix, `tests/regress_requisition_prior_review.py` and `tests/regress_review_intakes_own_stem.py` contain `from clutch.__main__ import main as clutch_main`, which matches that substring. So the test never checks that these two files contain `if __name__ == "__main__":`. Acceptance criterion 3 says each of the ten files must contain that line, checked by this test. The skip also lets any future script that imports `clutch.__main__` avoid the text check. (do instead: Remove the `if "from clutch.__main__ import main" not in ...` condition and assert `'if __name__ == "__main__":' in script.read_text()` for every globbed script. All 54 scripts now have the guard, including those that import `clutch_main`.)

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "36d2eb4720e6a9ffc0cfa7def483d9eba1e078b5",
  "stem": "regress-scripts-guarded",
  "reviewed_sha": "36d2eb4720e6a9ffc0cfa7def483d9eba1e078b5",
  "summary": "The ten scripts are guarded correctly and the earlier `main` shadowing is fixed with the `clutch_main` alias, but the new test skips the guard-line text check for two of the ten files, so acceptance criterion 3 is only partly met.",
  "findings": [
    {
      "code": "acceptance",
      "path": "tests/integration/test_regress_scripts_guarded.py",
      "line": 18,
      "message": "The test skips the guard-line check for any script whose text contains `from clutch.__main__ import main`. After the alias fix, `tests/regress_requisition_prior_review.py` and `tests/regress_review_intakes_own_stem.py` contain `from clutch.__main__ import main as clutch_main`, which matches that substring. So the test never checks that these two files contain `if __name__ == \"__main__\":`. Acceptance criterion 3 says each of the ten files must contain that line, checked by this test. The skip also lets any future script that imports `clutch.__main__` avoid the text check.",
      "paved_road": "Remove the `if \"from clutch.__main__ import main\" not in ...` condition and assert `'if __name__ == \"__main__\":' in script.read_text()` for every globbed script. All 54 scripts now have the guard, including those that import `clutch_main`.",
      "kind": null,
      "unit": null
    }
  ],
  "spec_version": "1.6",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "snag"
}
```
