## Outcome

ok

## Surprises / judgment calls

Candidate selection also consumes image judgments, so it now honors the declared presence mode while preserving the default call shape; focused mutation checks caught the tested wrong behaviors.

## Dead ends

The first full unit run exposed candidate-selection test fakes that accept only the original arguments; preserving the default call shape resolved it.

## Second problems filed

- box-000838-0328f75a: The out-of-scope docs/gemini-graphics-refactor-plan.md still describes the presence check as making no model call and using an expected-location crop.

## Resolved engine/model

- provider: codex
- model: gpt-6.1-terra
- spec: implement 2.20

## Predicted vs actual

The ticket estimated 25 minutes; elapsed time was not recorded.

