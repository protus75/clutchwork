---
id: declined-box-000727-3b2fba24
kind: declined
link: box-000727-3b2fba24
reopen_after_days: 60
---
On Linux, the `max_rss_kb` that the exec seam stores in each provider call's evidence `end.json` comes from `os.wait4` in `clutch/seams.py::_reap`. Exec carries the parent's memory high-water mark into the child, so the figure is the larger of the engine's peak and the provider's peak. Whenever the engine is the bigger process, it records the engine's size and not the provider's. The proposal is to spawn providers through a small spawner process, or to also record the engine's own peak at spawn so a child figure that does not exceed it can be marked unknown.

The measurement is real and reproducible: tickets/exec-seam-peak-memory-test/evidence/evidence.txt shows a child running `pass` under a 600 MB parent reporting the same 619036 KB as a child that allocates 200 MB. But this is already documented, current behavior, not a hidden gap. docs/how-clutch-works.md section 7.4 (line 774) says that on Linux `max_rss_kb` is the larger of the provider's peak and the engine's peak at spawn, and is the provider's own peak only when it exceeds the engine's. No engine code reads `max_rss_kb` to make a decision. It appears only in `clutch/seams.py`, `clutch/evidence/schema.py`, docs and tests, so no scheduling, gate, breaker or report goes wrong because of it. The flaky test that exposed this is already handled by the test-only ticket exec-seam-peak-memory-test. Changing the figure now would be a hardening of evidence accuracy with no runtime behavior to fix. Reopen when a consumer starts reading `max_rss_kb` for a decision or a published figure, such as a training export, a stats view or a memory-based limit.

- tickets/exec-seam-peak-memory-test/evidence/evidence.txt: child 'pass' under 600 MB parent = 619036 KB, same as child allocating 200 MB
- clutch/seams.py:216,237: Rusage built from os.wait4 ru_maxrss
- docs/how-clutch-works.md:774 already documents that on Linux max_rss_kb is max(engine peak at spawn, provider peak)
- Grep for max_rss in clutch/ finds only seams.py and evidence/schema.py; nothing reads it for a decision

Message: box-000727-3b2fba24
