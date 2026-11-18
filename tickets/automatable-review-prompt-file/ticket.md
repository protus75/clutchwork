---
state: confirmed
source: human
priority: P2
kind: chore
---

## Depends on
none

## Context
- docs/document-agent-plan.md

## Goal / Why
Make the complete Automatable review prompt directly readable as Markdown alongside the other review prompts, with one canonical body.

## Scope in / Scope out
Move the fenced prompt body from the document-agent plan appendix to the standalone file. Update the lens catalog source cell, section 4.3 and the implementation breakdown row to link directly to it. Keep the appendix heading as a stable anchor with a single link in place of its body. Preserve the role instructions and verdict definitions verbatim. This is a documentation extraction.

## Scope fence
- docs/review-prompts/AutomatableReview.md
- docs/document-agent-plan.md

## Acceptance criteria
1. Comparing `docs/review-prompts/AutomatableReview.md` against the pre-change appendix yields identical bytes between the opening and closing fence lines, including the author instructions, mechanical lint stage, synthesis, automation ratio, verdicts and disposition.
2. In `docs/document-agent-plan.md`, the catalog, section 4.3, implementation breakdown and retained appendix anchor all link to the standalone prompt. The appendix contains no duplicate prompt body.

## Verification
```
rg -Fx "# Dry-run author agent prompt (verbatim)" docs/review-prompts/AutomatableReview.md
rg -Fx "# Synthesis agent prompt (verbatim)" docs/review-prompts/AutomatableReview.md
rg -F "(review-prompts/AutomatableReview.md)" docs/document-agent-plan.md
```

## Definition of rejected
Reject a paraphrase, a prompt missing a role, or a second maintained body in the plan.

## Time budget
- expected: 3m
- stuck: 6m
