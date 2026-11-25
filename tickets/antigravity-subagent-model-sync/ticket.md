---
state: confirmed
source: human
priority: P1
kind: chore
---

## Depends on
- none

## Context
- docs/antigravity-plan.md#5. Supervising `drain` and `serve` in Antigravity (`ask-specs-mcp-supervision`)
- docs/antigravity-plan.md#Ticket breakdown

## Goal / Why
Roadmap row 234 (`antigravity-subagent-model-sync`). `docs/antigravity-plan.md` section 5 currently states that Antigravity `invoke_subagent` uses `Model: "flash"` for row authors (`clutch prompt author <stem>`), `roadmap gate` runners, and open-decision proposal agents, whereas the shipped process specs (`clutch/specs/ask/plan-ticket-drain.md` and `clutch/specs/ask/plan-ticket-serve.md`) already implement the owner's rule: use `Model: "inherit"` (or `"pro"` / a strong model, never `"flash"`) for row authors (`clutch prompt author <stem>`) and phase-closing reviews, and use `Model: "flash"` only for running `clutch roadmap gate <release>`. Updating `docs/antigravity-plan.md` section 5 (and aligning row 7 of its Ticket breakdown table) brings the plan into agreement with the shipped specs.

## Boundary contract
none
- reason: documentation correction without behavior change; only `docs/antigravity-plan.md` is updated so it matches the already-shipped process specs.

## Scope in / Scope out
Scope in:
- In `docs/antigravity-plan.md` section 5 (`### 5. Supervising \`drain\` and \`serve\` in Antigravity (\`ask-specs-mcp-supervision\`)`), update the **Explicit child-model routing across agent hosts** bullet so Antigravity `invoke_subagent` guidance states the exact shipped mapping: use `Model: "inherit"` (or `"pro"` / a strong model, never `"flash"`) for row authors (`clutch prompt author <stem>`) and phase-closing acceptance reviews, and use `Model: "flash"` only for `roadmap gate` runners (`clutch roadmap gate <release>`), keeping the Claude `Sonnet`-not-`Opus` rule and cross-family calibration/baseline panel note intact.
- In `docs/antigravity-plan.md` `#Ticket breakdown` row 7 (`ask-specs-mcp-supervision`), update the `flash`/`pro` phrase so it matches (`"inherit"`/`"pro"` for row authors and reviews, `"flash"` only for `roadmap gate` runners).

Scope out:
- Do not modify any shipped process specs, code, tests, or other documentation files.

## Scope fence
- docs/antigravity-plan.md

## Acceptance criteria
1. `docs/antigravity-plan.md` section 5 and Ticket breakdown row 7 specify Antigravity `Model: "inherit"` (or `"pro"`, never `"flash"`) for row authors and phase-closing reviews and `Model: "flash"` only for `roadmap gate` runners, with no remaining statement sending row authors to `"flash"`; verified by reviewer inspection of `git diff main...HEAD -- docs/antigravity-plan.md`.
2. Existing documentation checks continue to pass without regression; verified by `./dev.py test tests/unit/test_readme.py`.

## Verification
```
./dev.py test tests/unit/test_readme.py
```

## Definition of rejected
`docs/antigravity-plan.md` still routes row authors to `"flash"`, edits any file outside `docs/antigravity-plan.md`, or alters any other section of the plan.

## Time budget
- expected: 5m
- stuck: 10m
