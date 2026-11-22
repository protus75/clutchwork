---
state: confirmed
source: human
priority: P2
kind: chore
---

## Depends on
- none

## Context
- docs/roadmap.md
- clutch/specs/doc/facets/type/roadmap.md
- clutch/docs/host-authoring.md#Keeping tickets apart
- tickets/state-verdict-ticket-service/rework.md
- docs/api-image-provider-plan.md
- docs/remote-view-plan.md
- docs/training-backup-plan.md
- docs/mcp-server-notes.md

## Goal / Why
`docs/roadmap.md` has drifted behind the repo, and the owner asked for a refresh on 2026-11-22. The roadmap Type facet (`clutch/specs/doc/facets/type/roadmap.md`, the instructions `clutch prompt roadmap` prints) defines the maintenance procedure. When this ticket is done, the roadmap matches HEAD in four ways:

1. **Status is current.** The `## Status` section still describes the audit at `a59190cd` and the counts from "725 tickets merged ... as of 2026-11-19". It must name the HEAD commit it was refreshed at, the merged and in-flight counts from `clutch view status`, the blocked stems, and the pending Suggestion Box messages. The release status from `clutch roadmap status` at authoring time (2026-11-22) was: 0.3.0 gate passed; 0.4.0 has 58 rows merged and `roadmap merged --release 0.4.0` now prints ok, but its recorded gate result is a stale failure from 2026-11-20; 0.5.0 has 50 rows merged and its gate fails at `clutch training eval --route medium/review --holdout .clutch/training-eval/holdout.txt`; 0.6.0 has 1 row merged and 12 blocked; 0.7.0 has 13 blocked.
2. **Work done off the roadmap is recorded.** 242 stems merged on main since 2026-11-19 (taken from `clutch(<stem>)` commit subjects), and 160 of them appear nowhere in the roadmap. They fall into these families: the integration-I/O restoration (`integration-disk-io-skip`, `integration-io-guard`, `disk-io-skip-per-file`, `io-helpers-*`, `restore-helpers-*`, `restore-io-tests-01..39`, `shared-git-fake*`, `shared-fakes-guard`, `test-io-rules`, `test-tmp-in-checkout`); serve and parallel hardening (`serve-*`, `retro-check-once`, `drain-retro-check-once-per-settle`, `retro-due-one-owner`, `dispatch-during-driver-pass-drain`, `scheduler-ranks-full-priority`, `supervisor-orders-by-depends`); requisition review (`requisition-review-*`, `requisition-contract-review-comparison`); meta blocks (`meta-*`, `check-owns-meta-headers`, `check-meta-fill-nested-stage`, `implement-spec-meta-headers-from-verbs`); ticket-write commits (`*-ticket-writes-commit-edit`, `ticket-writes-atomic-commit`, `git-commit-edit-owner`, `ticket-write-serialization-proof`); extension (`extension-*`); the plan prompts (`plan-prompts-*`, `plan-ticket-serve-prompt`, `plan-subagents-explicit-sonnet`, `host-prompts`); and other fixes (image quality, provider parsers, hot paths, and the rest). Record them as merged work that came from outside the roadmap, without adding one master-table row per stem. Put a short per-family summary in `## Status` or a new subsection under `## 8`. Then re-check the section 2-4 audit findings the work touched: remove any finding it fixed, and mark any that recurred, as the facet's Maintenance paragraph requires. Example: section 2.6 and 3.5 claims about integration tests now that `integration-io-guard` and `REAL_IO_TESTS` exist.
3. **Unlisted plans are admitted or reported.** The roadmap does not mention `docs/api-image-provider-plan.md`, `docs/remote-view-plan.md`, `docs/training-backup-plan.md`, or `docs/mcp-server-notes.md`. Assess each against the facet's `## Admission` paragraph. A plan that qualifies gets master-table rows in the release it fits. The rows use fresh stems, unused row numbers, an Owner whose first word uniquely matches the plan filename (`api`, `remote`, `backup`), and Content that cites the plan section and its discriminating check. The roadmap also lists that plan in the `relates:` meta field and in the section 1 theme or a section 5 decision. A plan that does not qualify, including `mcp-server-notes.md` (a notes file, not a `*-plan.md`), is named in section 3 or 4 with the precise repair or decision it needs. It gets no ready row.
4. **Every `clutch roadmap status` wait is resolved or recorded.** Row 210 (`state-verdict-ticket-service`) is rejected in the journal. Read `tickets/state-verdict-ticket-service/rework.md`, then either give the row a fresh stem with Content that names the rejection's cause, or record why it stays held. Rows 75-77 use Owner `document plan N`, which matches no `docs/*-plan.md` filename. Fix the Owner so the driver can resolve it, for example by naming the owning plan's path in a way the parser accepts. If no form works because `docs/document-agent/plan.md` sits outside `docs/*-plan.md`, record that in section 3 and file it with `clutch box suggest` rather than editing `clutch/roadmap.py`.

This matters because the driver (`clutch prompt plan-ticket-drain`) reads this file as its work queue. While these waits are unresolved, the next drain has nothing it can author, and the plans added since the last refresh have no path into the pipeline.

## Boundary contract
none
- reason: documentation correction with no behavior change; `docs/roadmap.md` keeps the structure `clutch/roadmap.py` parses (section 1 bold release rows, `### <release>` headings with the eight-column table, fenced `gate`/`start` blocks), and no code, prompt spec or test changes.

## Scope in / Scope out
Scope in: edit `docs/roadmap.md` only, following the Maintenance paragraph of the roadmap Type facet listed in Context:
- Keep existing row numbers, stems, authored links, merged strikes, decisions, conditional gates, and release history.
- Give each new row an unused number and a stem that does not already exist under `tickets/` or in the journal.
- Update the `clutch:meta` block's `relates:` list for any newly admitted plan, then run `clutch meta refresh docs/roadmap.md` so `verified`/`hash` match.

Scope out:
- Authoring row tickets, running release gates, starting a drain, or editing any plan document, code, prompt spec, or test.
- A defect found in the roadmap parser or driver goes to `clutch box suggest`.
- No standing test or criterion pins roadmap text (host-authoring "Keeping tickets apart").

## Scope fence
- docs/roadmap.md

## Acceptance criteria
1. `uv run clutch roadmap status` exits 0 and prints no wait naming row 210, 75, 76 or 77 with the reasons quoted in Goal item 4. The only exception is a wait the roadmap's section 3 records as held, with its reason.
2. `uv run clutch meta check docs/roadmap.md` exits 0. A stale `hash` or a missing `relates:` path fails it.
3. One-time review check: `docs/roadmap.md` `## Status` names a HEAD commit from 2026-11-22 or later, not `a59190cd`. Each of `api-image-provider-plan.md`, `remote-view-plan.md`, `training-backup-plan.md`, and `mcp-server-notes.md` appears in `docs/roadmap.md`, checked with `grep -c` for each name returning at least 1.
4. One-time review check: each new master-table row has a stem that appears exactly once in `docs/roadmap.md` and has no existing `tickets/<stem>/` directory.

## Verification
```
uv run clutch roadmap status
uv run clutch meta check docs/roadmap.md
```

## Definition of rejected
- Any file other than `docs/roadmap.md` changes.
- An existing row number or stem is renumbered or renamed, except a fresh stem for rejected row 210.
- A merged strike or owner decision is dropped.
- A master-table row is added for each off-roadmap merged stem instead of a per-family summary.
- A plan that does not qualify gets a ready row.

## Time budget
- expected: 30m
- stuck: 60m
