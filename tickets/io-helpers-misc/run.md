## Outcome

ok

## Surprises / judgment calls

Final sequential verification passed: 18 helper tests and 2162 unit tests; base and candidate integration runs both reported 297 passed and 3341 skipped. Focused compatibility tests: 5 passed. Box retains caller-root filesystem I/O because its reads bypass the filesystem seam; Rig uses shared in-memory fakes as required.

## Dead ends

Using FakeFileSystem for Box lost queued messages because Box reads paths directly; retained its permitted caller-root disk I/O without changing production code.

## Second problems filed

- box-001127-eb9fd8cb: docs/roadmap.md:102 still states that test_drain.py imports commit_lock from test_git.py; that import now comes from tests.misc_helpers.

## Resolved engine/model

- provider: codex
- model: gpt-6.1-sol
- spec: implement 2.27

## Predicted vs actual

30m expected; approximately 9m actual.

