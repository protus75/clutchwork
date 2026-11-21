## Outcome

premise_failed

## Surprises / judgment calls

The ticket verification passed with 60 tests; the full integration suite failed only tests/integration/test_engine_text_verbs.py::test_no_engine_text_names_dev_py. That test also failed in isolation on the candidate and passed on the base. The exact ticket verification cannot run on the base because the new test file does not exist there.

## Dead ends

Added the required literal paved road; the existing engine-text check forbids dev.py anywhere under clutch/. The existing check prevents recurrence of repo-specific commands in installed engine text.

## Second problems filed

none

## Resolved engine/model

- provider: codex
- model: gpt-6.1-terra
- spec: implement 2.23

## Predicted vs actual

Ticket expected 15 minutes; actual not measured.

