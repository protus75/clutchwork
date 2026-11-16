---
id: declined-box-000540-944b57a8
kind: declined
link: box-000540-944b57a8
reopen_after_days: 30
---
An audit of driver-loop found that a malformed docs/roadmap.md ticket row gets past roadmap.parse and roadmap.choose as ready and then crashes the driver step. The bad rows are a blank Content cell, number 0, or a row above the first '### ' release heading. author_ahead builds a box.RoadmapRow, whose NonBlank and ge=1 fields raise a pydantic ValidationError. roadmap.drive catches only Refusal, so the error escapes Drain._run_driver and Serve.run_driver. The proposal has two parts: choose/author_ahead turns a payload that fails validation into a Wait, and the driver step reports any other error in the digest and keeps going instead of stopping the engine.

The code path is real. parse accepts cells[0]=='0' through isdigit, keeps an empty Content cell, and sets release to '' for rows before any '### ' heading. choose checks only kind, priority, the plan owner, depends and evidence. RoadmapRow(...) in author_ahead sits outside any handler, and drive's try blocks catch only Refusal. But this is hardening against malformed input that has not been seen. The message cites no drain or serve run that crashed this way, and no current roadmap row with these defects. docs/roadmap.md is a committed, reviewed document, and the failure is loud (a traceback), not silent, so the operator can correct the row. Record 000286 (a malformed YAML tag escaping load_config as ValueError instead of ConfigError) was declined on the same grounds. The second half, letting the driver step swallow every non-Refusal error, is a broad policy change that would hide real engine defects, and it is not bounded to one fix. Reopen if a drain or serve start fails on a ValidationError from roadmap.author_ahead, or a committed roadmap row reaches choose().ready with a blank Content, number 0, or empty release.

- clutch/roadmap.py:87-95 parse accepts any digit string as the number (including 0), any Content cell (including blank), and release='' before the first '### ' heading
- clutch/roadmap.py:215-241 choose never checks number, release or content before marking a row ready
- clutch/roadmap.py:278-289 author_ahead builds RoadmapRow outside any exception handler
- clutch/box.py:67-77 RoadmapRow: number ge=1, release and content NonBlank
- clutch/roadmap.py:518-522 drive catches only Refusal around author_ahead and ship
- clutch/drain.py:412-416 and clutch/serve.py:362-369 call the driver step with no handler for other exceptions
- No run, journal event or current roadmap row showing the crash is cited
- Precedent: declined-box-000286-3f10ef53 (malformed input escaping as a non-refusal exception, declined as unobserved hardening)

Message: box-000540-944b57a8
