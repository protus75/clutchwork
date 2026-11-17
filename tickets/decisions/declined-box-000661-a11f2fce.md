---
id: declined-box-000661-a11f2fce
kind: declined
link: box-000661-a11f2fce
reopen_after_days: 30
---
The Author stem gate (`clutch/author.py::AuthorGate`) treats a stem as used when any journal event names it. `clutch/roadmap.py::choose` treats a stem as used only when it has a state transition. The message asks for one 'stem in use' predicate, owned by one module, that both call. Before the fix, this mismatch let the driver mark rows 21 and 114 ready, and Author then declined them on every re-file (box-000635/636/637/639/644).

The harmful behavior the message cites is already fixed by the merged ticket roadmap-named-stem-refile. In `clutch/roadmap.py::drive`, the driver builds `named` from every journal event's ticket. Before it sends any ready row to Author, it re-files a row whose stem is in `named` but has no state transition under a fresh stem, chosen with `fresh_stem` against `taken`. A row's stem that Author would refuse now gets renamed before Author sees it, so the decline loop the message describes can no longer happen through the driver. `choose` has two other callers. `clutch/acceptance.py` uses only its strike list. `roadmap.status` can list such a row under 'next' before the driver renames it, which is a small display difference and changes no runtime decision. What remains is a consolidation refactor: one shared predicate in place of a gate plus a driver-side guard. That is a cleanup with no current incorrect runtime behavior behind it. Reopen if Author again refuses a stem as 'already named in the journal' for a row the driver marked ready after roadmap-named-stem-refile merged, or if a new caller of `choose` sends ready rows to Author without the named-stem re-file.

- clutch/author.py:98-99 AuthorGate refuses a stem when any journal event's ticket equals it
- clutch/roadmap.py:225-226 choose waits only on rows whose stem has a state in `states`
- clutch/roadmap.py:352-353 drive builds `named` from all journal event tickets and adds it to `taken`
- clutch/roadmap.py:392-399 drive re-files a ready row whose stem is in `named` with no state, using fresh_stem, before sending it to Author
- roadmap-named-stem-refile is in the merged set
- clutch/roadmap.py:489,515 status uses choose's ready list for display only; clutch/acceptance.py:84 uses only `.strike`

Message: box-000661-a11f2fce
