# Review: snag

The prior test_triage finding is fixed and the rename is otherwise complete, but the updated ticketless test in test_llm_effect.py passes a `subject` keyword that its local `run` helper does not accept, so the full suite fails.

## Findings

- [logic] tests/integration/test_llm_effect.py:188 `test_ticketless_surface_keys_on_its_surface_name` now calls `run(driver, ticket=None, subject="ticketless")`, but this file's helper is `def run(driver: Driver, ticket: str | None = "t-echo", attempt: int = 1)` at line 88. The diff leaves that helper unchanged, so it has no `subject` parameter. The call raises `TypeError: run() got an unexpected keyword argument 'subject'`. The helper also never forwards a subject to `driver.run`, so the call would still hit the new ticketless `ValueError` even without the TypeError. Criterion 6 (`./dev.py test` passes on the full suite) is unmet. (do instead: Extend the helper at tests/integration/test_llm_effect.py:88 to take `subject: str | None = None` and pass `subject=subject` to `driver.run`. Or call `driver.run` directly in this test with `ticket=None, subject="ticketless"`.)

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "a7ba155c1e34c5f931fb19cc41db2735d24301c4",
  "stem": "llm-request-subject",
  "reviewed_sha": "a7ba155c1e34c5f931fb19cc41db2735d24301c4",
  "summary": "The prior test_triage finding is fixed and the rename is otherwise complete, but the updated ticketless test in test_llm_effect.py passes a `subject` keyword that its local `run` helper does not accept, so the full suite fails.",
  "findings": [
    {
      "code": "logic",
      "path": "tests/integration/test_llm_effect.py",
      "line": 188,
      "message": "`test_ticketless_surface_keys_on_its_surface_name` now calls `run(driver, ticket=None, subject=\"ticketless\")`, but this file's helper is `def run(driver: Driver, ticket: str | None = \"t-echo\", attempt: int = 1)` at line 88. The diff leaves that helper unchanged, so it has no `subject` parameter. The call raises `TypeError: run() got an unexpected keyword argument 'subject'`. The helper also never forwards a subject to `driver.run`, so the call would still hit the new ticketless `ValueError` even without the TypeError. Criterion 6 (`./dev.py test` passes on the full suite) is unmet.",
      "paved_road": "Extend the helper at tests/integration/test_llm_effect.py:88 to take `subject: str | None = None` and pass `subject=subject` to `driver.run`. Or call `driver.run` directly in this test with `ticket=None, subject=\"ticketless\"`.",
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
