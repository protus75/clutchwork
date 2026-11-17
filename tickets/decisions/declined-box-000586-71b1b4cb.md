---
id: declined-box-000586-71b1b4cb
kind: declined
link: box-000586-71b1b4cb
reopen_after_days: 14
---
The suggestion asks for one bullet in the host authoring guide (`clutch/docs/host-authoring.md`) telling authors to cite code by symbol (`path.py::Name`), heading or exact text, never by line number or literal version, and to state values relative to main at the base commit. The trigger is a 0.3.0 plan-run ticket that drifted after a sibling merge bumped a spec it cited by version and line numbers. The open ticket plan-drain-prompts leaves this rule out of its prompt and points to this message instead.

This is guidance for authors, not a fix for engine behavior that is wrong at runtime. The guide already gives the symbol and heading selection syntax for Context (`path.py::Name`, `path.py::Class.method`, `path.md#Heading`). Part of the request is therefore already covered, and the rest is a style rule for prose and criteria. The only incident given is one drifted ticket, described in an evidence note. The note names no stem, no park or failed run caused by a line-number citation, and no cost in caps. A close precedent, declined-box-000584-1803a09f, asked for a guide rule against citing roadmap rows by literal number and was declined even though it had a concrete near-miss. Reopen if a run is parked, snagged or failed because a ticket cited code or a spec by line number or literal version that a sibling merge then changed, and the stem and its artifacts are named; or if the owner asks directly for this guide change.

- clutch/docs/host-authoring.md:44-46 already tells authors to select Context code with `path.py::Name` / `path.py::Class.method` and headings with `path.md#Heading`
- tickets/plan-drain-prompts/evidence/large-automated-effort.md:112-113 reports one drifted ticket but gives no stem, outcome or cost
- tickets/plan-drain-prompts/ticket.md:53 and :161 defer the rule to box-000586 instead of putting it in the prompt
- declined-box-000584-1803a09f declined a matching guide rule against literal row-number citations

Message: box-000586-71b1b4cb
