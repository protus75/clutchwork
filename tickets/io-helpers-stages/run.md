## Outcome

ok

## Surprises / judgment calls

The hub retains its existing build_config import for the config-adoption check. Final verification passed: 19 helper unit tests, 1 helper integration test, 2005 unit tests, and 294 integration tests with 3339 skipped. The separate shared-fakes and skip-list checks also passed. The base integration count was not independently measured.

## Dead ends

An initial fake Git response caused core-drift findings; the helper now returns file-based blob identities and reports absent files through GitError.

## Second problems filed

none

## Resolved engine/model

- provider: codex
- model: gpt-6.1-terra
- spec: implement 2.27

## Predicted vs actual

30 minutes expected; elapsed time not recorded.

