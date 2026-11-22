# Review: snag

The Status refresh, the family summary and the plan assessments match the ticket, but the diff deletes a section 2.6 audit finding that still holds and cites a Suggestion Box id that exists only in the run worktree.

## Findings

- [acceptance] docs/roadmap.md:105 The diff deletes the section 2.6 finding 'Several test modules double as fixture libraries' as if it were fixed. HEAD still has the problem: `tests/integration/test_drain.py:35` runs `from tests.integration.test_git import commit_lock`, so a test module is still a fixture library. The facet's Maintenance paragraph and Goal item 2 say to remove only findings the work fixed and to mark findings that recurred. The new paragraph at line 105 covers only the shared-fakes and fixture-builder duplication, not this one. (do instead: Put the fixture-library bullet back, updated to the current case (`test_drain.py` imports `commit_lock` from `tests/integration/test_git.py`), and keep its '(recurred in 0.5.0)' mark. Delete only the part about `test_merge.py`, which no longer applies.)
- [logic] docs/roadmap.md:117 The held-rows record for rows 75-77 says 'Filed as `box-000001-40a689e9` in this worktree's Suggestion Box'. The disposable run worktree's box does not merge to main, so the roadmap would cite a message id nobody can find. The parser defect would then have no lasting record beyond this sentence. (do instead: Leave out the worktree-local box id. Describe the parser limitation and the needed repair (nested-plan resolution in `clutch/roadmap.py::plan_path`) in section 3, and say it still has to be filed as a suggestion on main. Alternatively, cite a box message that exists on main.)

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "78c11c6f5d6bd381c6c6434a4f0e6155e1c9343c",
  "stem": "roadmap-freshen-2026-11-22",
  "reviewed_sha": "78c11c6f5d6bd381c6c6434a4f0e6155e1c9343c",
  "summary": "The Status refresh, the family summary and the plan assessments match the ticket, but the diff deletes a section 2.6 audit finding that still holds and cites a Suggestion Box id that exists only in the run worktree.",
  "findings": [
    {
      "code": "acceptance",
      "path": "docs/roadmap.md",
      "line": 105,
      "message": "The diff deletes the section 2.6 finding 'Several test modules double as fixture libraries' as if it were fixed. HEAD still has the problem: `tests/integration/test_drain.py:35` runs `from tests.integration.test_git import commit_lock`, so a test module is still a fixture library. The facet's Maintenance paragraph and Goal item 2 say to remove only findings the work fixed and to mark findings that recurred. The new paragraph at line 105 covers only the shared-fakes and fixture-builder duplication, not this one.",
      "paved_road": "Put the fixture-library bullet back, updated to the current case (`test_drain.py` imports `commit_lock` from `tests/integration/test_git.py`), and keep its '(recurred in 0.5.0)' mark. Delete only the part about `test_merge.py`, which no longer applies.",
      "kind": null,
      "unit": null
    },
    {
      "code": "logic",
      "path": "docs/roadmap.md",
      "line": 117,
      "message": "The held-rows record for rows 75-77 says 'Filed as `box-000001-40a689e9` in this worktree's Suggestion Box'. The disposable run worktree's box does not merge to main, so the roadmap would cite a message id nobody can find. The parser defect would then have no lasting record beyond this sentence.",
      "paved_road": "Leave out the worktree-local box id. Describe the parser limitation and the needed repair (nested-plan resolution in `clutch/roadmap.py::plan_path`) in section 3, and say it still has to be filed as a suggestion on main. Alternatively, cite a box message that exists on main.",
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
