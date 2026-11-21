## Outcome

ok

## Surprises / judgment calls

Retro, supervise, box intake, maintenance, startup, and verdict settlement retain exclusive admission because their ownership is outside this ticket; verdict settlement is assigned to serve-confirm-during-check. The existing locks were sufficient, so no new lock was added. Ticket verification passed all 58 tests, the unit coverage gate passed 1,823 tests, and a full integration run passed 3,601 tests. A later full integration run timed out in one admission test; it passed alone and the subsequent full ticket verification passed. The exact base verification command could not collect because the two new test files do not exist on the base; the affected test passed alone there. The regression reproducer reported defect on the base and pass on the candidate. Mutation checking confirmed the original scan and watcher implementations fail the new lock assertions; individual mutations were not completed for every assertion.

## Dead ends

The first mutation run used the original watcher implementation and left its test waiting after an assertion failure; the test was adjusted to expose that failure without hanging.

## Second problems filed

- box-000983-96a0ff93: The precheck admission integration test timed out intermittently during the full integration suite, then passed in isolation and in the subsequent ticket verification.
- box-000984-64d4b65f: The repository-wide metadata check reports pre-existing drift in docs/roadmap.md and an empty purpose in tests/unit/test_training_triage_records.py, both also present on the base commit.

## Resolved engine/model

- provider: codex
- model: gpt-6.1-terra
- spec: implement 2.23

## Predicted vs actual

The ticket estimated 30 minutes; the work took less than that.

