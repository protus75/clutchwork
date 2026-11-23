---
id: tombstone-box-000937-c84fd444
kind: tombstone
link: check-owns-meta-headers
reopen_after_days: 14
---
A retro finding says Implement twice returned a false premise_failed because `clutch meta check` reported `drifted` on files the diff changes. That happened on context-suggest-author-block attempt 0 and spools-tests-via-helper-fake-fs attempt 0. The finding blamed step 5 of clutch/specs/implement.md for telling the implementer to confirm that no changed file is `drifted`. It asked step 5 to limit the check to added files and to say that drift on changed files is expected because Check refreshes those headers.

The requested repair is already on main. Step 5 of clutch/specs/implement.md (line 47) now says the implementer never adds, edits or refreshes a `clutch:meta` header. It also says never to run `clutch meta refresh`, `meta fill` or `meta check` for the diff, that Check writes headers for every file the diff adds or changes, and that a meta finding on an untouched file goes to `second_problems`. The step-5 instruction to confirm no changed file is `drifted`, which caused both bounces, is gone. Stopping the implementer from treating meta state as a premise is exactly what the merged check-owns-meta-headers ticket set up. Reopen if a run after this spec text still returns premise_failed on a meta finding.

- clutch/specs/implement.md:47 step 5: 'Never add, edit, copy or refresh a `clutch:meta` header, and never run `clutch meta refresh`, `clutch meta fill` or `clutch meta check` for the diff. Check writes headers for every file the diff adds or changes.'
- clutch/stages.py:1722 check_meta runs in Check and emits meta_drift findings
- clutch/gates.py:33 SOFT_GATE_DEFAULTS = {"meta_drift"}
- merged stem check-owns-meta-headers

Message: box-000937-c84fd444
