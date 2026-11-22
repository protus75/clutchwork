## Outcome

premise_failed

## Surprises / judgment calls

Base: 2045 unit passed; integration 296 passed, 3339 skipped. Candidate: 2074 unit passed, including 29 helper checks; integration 295 passed, 3339 skipped, one guard failure. The exact integration command passed again in a full-history base worktree. Import checks and mutation checks passed.

## Dead ends

Moving VALID verbatim, as permitted, triggers both a missing exemption for its new owner and a stale exemption for its former owner; build_config cannot reproduce its review and merge sections byte-for-byte.

## Second problems filed

- box-001112-ce4cf299: docs/roadmap.md:97–98 would retain stale helper ownership statements after this extraction.

## Resolved engine/model

- provider: codex
- model: gpt-6.1-sol
- spec: implement 2.27

## Predicted vs actual

none

