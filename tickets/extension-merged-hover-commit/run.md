## Outcome

ok

## Surprises / judgment calls

The repository marks all 31 tests in tests/integration/test_watch.py as skipped. Mutation checks detected the wrong behaviors covered by the new assertions; the simpler approach of composing the tooltip in JavaScript was rejected because the snapshot owns the displayed value.

## Dead ends

An initial mutation used a same-length edit that reused cached Python bytecode; a distinct-length mutation detected the regression.

## Second problems filed

none

## Resolved engine/model

- provider: codex
- model: gpt-6.1-terra
- spec: implement 2.27

## Predicted vs actual

none

