# Review: snag

The normalizer, the redacted real fixture (it matches the 80-line phase3-continue-14/codex-0006 capture, including the turn.completed usage line) and the unit tests meet the acceptance criteria, but the fixture integration test reads its file through a path that depends on the working directory.

## Findings

- [logic] tests/integration/test_evidence_codex_fixture.py:8 `Path("tests/fixtures/evidence/codex/stream.jsonl")` is resolved against the process working directory, not the repo. Running pytest from any other directory (an IDE runner, a subdirectory, a different rootdir) gives FileNotFoundError, even though the fixture and normalizer are correct. Other integration tests in this repo avoid this by anchoring on `Path(__file__)`, for example `tests/integration/test_diagnose_eval.py:20` and `test_eval_harness.py:21`. (do instead: Anchor the path on the test file: `Path(__file__).resolve().parents[1] / "fixtures" / "evidence" / "codex" / "stream.jsonl"`.)

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "3294e5bbce734e646de98e94b1b7f78575a81641",
  "stem": "evidence-normalize-codex",
  "reviewed_sha": "3294e5bbce734e646de98e94b1b7f78575a81641",
  "summary": "The normalizer, the redacted real fixture (it matches the 80-line phase3-continue-14/codex-0006 capture, including the turn.completed usage line) and the unit tests meet the acceptance criteria, but the fixture integration test reads its file through a path that depends on the working directory.",
  "findings": [
    {
      "code": "logic",
      "path": "tests/integration/test_evidence_codex_fixture.py",
      "line": 8,
      "message": "`Path(\"tests/fixtures/evidence/codex/stream.jsonl\")` is resolved against the process working directory, not the repo. Running pytest from any other directory (an IDE runner, a subdirectory, a different rootdir) gives FileNotFoundError, even though the fixture and normalizer are correct. Other integration tests in this repo avoid this by anchoring on `Path(__file__)`, for example `tests/integration/test_diagnose_eval.py:20` and `test_eval_harness.py:21`.",
      "paved_road": "Anchor the path on the test file: `Path(__file__).resolve().parents[1] / \"fixtures\" / \"evidence\" / \"codex\" / \"stream.jsonl\"`.",
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
