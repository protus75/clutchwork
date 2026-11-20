## Outcome

premise_failed

## Surprises / judgment calls

The same full verification command passed on the untouched base commit; the candidate failure also reproduced when the safety scenario ran alone. Instrumentation showed dispatch repeatedly reaching an idle point with tickets pending, then finding an exclusive admission section held or waiting after supervision. The ticket requires supervision before dispatch and prohibits selection during exclusive admission, but permits no admission arbitration change. The changes remain uncommitted.

## Dead ends

Changing the dispatch guard to recheck exclusive admission after supervision preserved the required exclusion but left selection starved in the admission scenarios.

## Second problems filed

none

## Resolved engine/model

- provider: codex
- model: gpt-6.1-terra
- spec: implement 2.20

## Predicted vs actual

Expected 55 minutes; work stopped before completion.

