---
id: declined-box-000493-bc44dcf5
kind: declined
link: box-000493-bc44dcf5
reopen_after_days: 30
---
The `review`, `confirm` and `reject` verbs accept one or more stems (`nargs="+"` in `clutch/__main__.py::_parser`). `main` handles the stems in order and returns at the first one that gives a nonzero result. The verb table in `docs/how-clutch-works.md` section 2.1 and the run guide `clutch/docs/host-running.md` describe each verb as taking a single stem or acting on 'the named ticket'. Neither document says a verb takes several stems or stops at the first failure.

This is a mismatch between the docs and the code, not wrong runtime behavior. The code works as written: a single-stem call does exactly what the docs say, and a multi-stem call handles each stem in order and returns the first nonzero code. Neither document is wrong for the single-stem form; they just don't mention the multi-stem form. The report names no run, operator action or extension call that went wrong because of it, so it does not meet the bar of a current, harmful behavior gap. Reopen if someone shows harm, for example an operator or supervising session that skipped later stems' verdicts because a multi-stem `confirm`/`reject`/`review` stopped at an earlier stem's nonzero result without saying so, or a caller that relied on the documented single-stem form and got the wrong result.

- clutch/__main__.py:275 gives `review` a `stems` argument with nargs='+'; clutch/__main__.py:300 does the same for `confirm` and `reject`.
- clutch/__main__.py:617-626 loops over args.stems for confirm/reject and review, and returns the first nonzero result, so later stems are never processed.
- docs/how-clutch-works.md:73-74 documents `confirm <stem> [--yes|--extension]` and `reject <stem> [--yes|--extension]` as taking one stem.
- clutch/docs/host-running.md:33,43,44 says review, confirm and reject act on 'the named ticket'.
- The message cites no failed run, misled operator or wrong verdict caused by this mismatch; the single-stem behavior the docs describe matches the code.

Message: box-000493-bc44dcf5
