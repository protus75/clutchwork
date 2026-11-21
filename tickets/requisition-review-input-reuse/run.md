## Outcome

premise_failed

## Surprises / judgment calls

Those tests patch or inspect the existing module-level review_ticket call sites; retaining a compatibility path would conflict with the ticket's requirement to migrate every production caller and avoid parallel legacy paths.

## Dead ends

Inspected all review_ticket references and the affected test call sites; no files were edited.

## Second problems filed

none

## Resolved engine/model

- provider: codex
- model: gpt-6.1-terra
- spec: implement 2.23

## Predicted vs actual

none

