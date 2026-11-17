# Review: snag

Two scripts now define a local `main()` that shadows the `main` they import from `clutch.__main__`, so the inner calls `main([...], cwd=..., env=...)` recurse into the zero-argument wrapper and raise TypeError; run as scripts, both fail with a traceback instead of printing their JSON line, which the ticket's Definition of rejected forbids.

## Findings

- [logic] tests/regress_requisition_prior_review.py:100 `def main() -> None:` (line 75) shadows `from clutch.__main__ import main` (line 12). `first = main(["review", "candidate"], cwd=repo, env=env)` now calls the new zero-argument wrapper and raises TypeError. Run as a script, the file no longer prints `{"regression_result": ...}` or keeps its exit code, which the Definition of rejected forbids. (do instead: Name the wrapper something that does not collide (for example `def run() -> None:` called from the `__main__` guard), or import the CLI entry under an alias (`from clutch.__main__ import main as clutch_main`) and call that inside the wrapper.)
- [logic] tests/regress_requisition_prior_review.py:105 `second = main(["review", "candidate"], cwd=repo, env=env)` has the same problem: `main` now points to the new local wrapper, not `clutch.__main__.main`. (do instead: Rename the wrapper or alias the imported `clutch.__main__.main` so this call reaches the CLI entry point.)
- [logic] tests/regress_review_intakes_own_stem.py:99 `def main() -> None:` (line 75) shadows `from clutch.__main__ import main` (line 12). `result = main(["review", "alpha"], cwd=repo, env=env)` now calls the zero-argument wrapper and raises TypeError, so running the script no longer prints its JSON result or keeps its exit code. (do instead: Rename the wrapper (for example `run()`) or import the CLI entry as `clutch_main` and call that inside the wrapper.)

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "7a2f2c446ca0325d2f9a467b490e5470db619a83",
  "stem": "regress-scripts-guarded",
  "reviewed_sha": "7a2f2c446ca0325d2f9a467b490e5470db619a83",
  "summary": "Two scripts now define a local `main()` that shadows the `main` they import from `clutch.__main__`, so the inner calls `main([...], cwd=..., env=...)` recurse into the zero-argument wrapper and raise TypeError; run as scripts, both fail with a traceback instead of printing their JSON line, which the ticket's Definition of rejected forbids.",
  "findings": [
    {
      "code": "logic",
      "path": "tests/regress_requisition_prior_review.py",
      "line": 100,
      "message": "`def main() -> None:` (line 75) shadows `from clutch.__main__ import main` (line 12). `first = main([\"review\", \"candidate\"], cwd=repo, env=env)` now calls the new zero-argument wrapper and raises TypeError. Run as a script, the file no longer prints `{\"regression_result\": ...}` or keeps its exit code, which the Definition of rejected forbids.",
      "paved_road": "Name the wrapper something that does not collide (for example `def run() -> None:` called from the `__main__` guard), or import the CLI entry under an alias (`from clutch.__main__ import main as clutch_main`) and call that inside the wrapper.",
      "kind": null,
      "unit": null
    },
    {
      "code": "logic",
      "path": "tests/regress_requisition_prior_review.py",
      "line": 105,
      "message": "`second = main([\"review\", \"candidate\"], cwd=repo, env=env)` has the same problem: `main` now points to the new local wrapper, not `clutch.__main__.main`.",
      "paved_road": "Rename the wrapper or alias the imported `clutch.__main__.main` so this call reaches the CLI entry point.",
      "kind": null,
      "unit": null
    },
    {
      "code": "logic",
      "path": "tests/regress_review_intakes_own_stem.py",
      "line": 99,
      "message": "`def main() -> None:` (line 75) shadows `from clutch.__main__ import main` (line 12). `result = main([\"review\", \"alpha\"], cwd=repo, env=env)` now calls the zero-argument wrapper and raises TypeError, so running the script no longer prints its JSON result or keeps its exit code.",
      "paved_road": "Rename the wrapper (for example `run()`) or import the CLI entry as `clutch_main` and call that inside the wrapper.",
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
