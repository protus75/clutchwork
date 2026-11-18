---
state: confirmed
source: human
priority: P2
kind: chore
---

## Depends on
none

## Context
- docs/document-agent/plan.md#1. Dimensions and facets
- docs/how-clutch-works.md#2.1 Verbs
- CHANGELOG.md#0.4.1

## Goal / Why
A release author can select a first-pass Release notes type and turn local release evidence into a reader-facing account of shipped changes and upgrade actions.

## Scope in / Scope out
Add the Release notes Markdown design example and list its type identifier and relative link in section 1 of docs/document-agent/plan.md. Keep release generation, runtime facet loading, and publication outside this documentation change.

## Scope fence
- docs/document-agent/type/release-notes.md
- docs/document-agent/plan.md

## Acceptance criteria
1. The Type row and first-pass prompt link in `docs/document-agent/plan.md` use the identifier `release-notes` and resolve to the new file.
2. `docs/document-agent/type/release-notes.md` declares facet type/release-notes, version "0.1", empty aliases and requires lists, and applies_to [create, derive].
3. The prompt in `docs/document-agent/type/release-notes.md` orders its output by release identity and status, reader-visible changes and fixes, upgrade actions, then applicable known issues. It asks for the affected reader, old and new behavior, and supported migration instructions for breaking changes.
4. `docs/document-agent/type/release-notes.md` requires local evidence for release membership, version, date, publication status and each substantive claim. It distinguishes a local tag from publication, keeps roadmap proposals out of shipped changes, groups related ticket entries by observable effect, and leaves unsupported claims out. It treats an empty changelog section as insufficient evidence to claim that nothing changed.

## Verification
```
rg -F "type/release-notes" docs/document-agent/type/release-notes.md
rg -F "(type/release-notes.md)" docs/document-agent/plan.md
```

## Definition of rejected
Reject a changelog rewrite, a runtime release command, or a prompt that presents planned work as released.

## Time budget
- expected: 4m
- stuck: 8m
