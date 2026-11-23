---
id: declined-box-001105-1e1887ec
kind: declined
link: box-001105-1e1887ec
reopen_after_days: 30
---
Author could not produce a ticket.

Evidence: - ticket_schema: `## Depends on` line 'None' is not a `- ` bullet (do instead: write `## Depends on` as one `- ` bullet per entry)
- ticket_schema: missing or empty body section `## Depends on` (do instead: add a non-empty `## Depends on` section)
- fence-incomplete: Scope in tells the implementer to grep tests/ and docs/ for SOFT_GATE_DEFAULTS and meta_drift and add any file asserting the soft default to the fence. Flipping the default forces edits to those files, so the fence must name them up front. A fence the implementer grows during the run makes the ticket impossible if any hit sits outside it, such as a docs page or a Check or stage test that expects meta_drift to pass softly. (do instead: Do the grep during authoring. List every file that pins the soft meta_drift default, whether a test or a document such as docs/how-clutch-works.md, in Scope fence and Context. If none exist, say so in Scope in and drop the conditional wording.)
- missing-context: Acceptance criteria 2 and 3 call `check_severity` in clutch/stages.py. Its signature, and how it reads a ticket's `gate_bypass`, are not in Context. The test's expected inputs and outputs can't be checked against merged code. (do instead: Add clutch/stages.py::check_severity to Context. Then state in criterion 2 the exact call, with its arguments and the ticket or Frontmatter it takes.)
- ticket_schema: documents named in Scope in are not fenced: docs/annotations-index-plan.md, docs/roadmap.md (do instead: fence the document and say which part to update, or drop the mention)
