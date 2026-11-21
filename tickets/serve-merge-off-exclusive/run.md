## Outcome

ok

## Surprises / judgment calls

The ticket verification passed with 95 tests; the standalone reproducer passed on the candidate and reported the defect on the base. Unit coverage passed. The full integration suite passed once on the candidate and once on the base; later intermittent failures passed in isolation, and the ticket verification passed again. Targeted mutation checks exercise the admission, exclusion, busy-state, commit-lock, and merge-call behavior.

## Dead ends

An initial integration fixture used invalid one-character ticket stems; using valid stems fixed the fixture.

## Second problems filed

- box-001018-5184bf51: Three host-loop tests had shared setup errors in one full integration run, but passed in isolation and in the subsequent full run.
- box-001019-1b30fac9: The integration variant of test_serve_admission_refusal_keeps_main_green timed out in a later full integration run, but passed in isolation and in the subsequent ticket verification.
- box-001020-44d979f0: The base has a drifted metadata header in docs/roadmap.md and an empty metadata purpose in tests/unit/test_training_triage_records.py.
- box-001021-44ec8a54: The out-of-fence docs/engine-state-db-plan.md still describes merge polling as entering exclusive admission.

## Resolved engine/model

- provider: codex
- model: gpt-6.1-terra
- spec: implement 2.23

## Predicted vs actual

none

