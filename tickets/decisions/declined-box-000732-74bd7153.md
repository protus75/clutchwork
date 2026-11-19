---
id: declined-box-000732-74bd7153
kind: declined
link: box-000732-74bd7153
reopen_after_days: 30
---
In provider evidence records, clock.mono_start_ns and clock.mono_end_ns are filled from the engine clock seam's wall-clock datetime as epoch nanoseconds, not from a monotonic counter. clock.wall_ms and the raw.stdout_times offsets are also differences of wall-clock readings, so a system clock step during a provider call would skew them. The planning document docs/evidence-trail-plan.md describes these values as monotonic.

The code matches the note: clutch/providers.py lines 451 and 539 compute int(<seam datetime>.timestamp() * 10**9). But docs/how-clutch-works.md, the maintained description of the code, already says that both mono_* fields hold the clock seam's wall time as epoch nanoseconds, not a monotonic counter. So the current documentation is accurate, and the only text that disagrees is the planning document. The real-world effect is limited to wrong values when the wall clock steps (NTP or manual) during one provider call. The message cites no recorded call where that happened and no consumer that made a wrong decision from such a value. That makes it a field-naming/plan-wording mismatch plus speculative hardening, not a demonstrated harmful behavior gap. Reopen within the window if an evidence record shows skewed or negative timing caused by a clock step, or when a consumer such as latency, stall or pacing analysis, the training export, or a normalizer starts reading mono_* or stdout_times as monotonic.

- clutch/providers.py:451 writes mono_start_ns as int(started.timestamp() * 10**9)
- clutch/providers.py:539 writes mono_end_ns the same way and computes wall_ms as (ended - started)
- docs/how-clutch-works.md:773 already says both mono_* fields are the engine clock seam's wall time as epoch nanoseconds, not a monotonic counter
- docs/evidence-trail-plan.md:125 (planning doc) describes stdout_times as monotonic nanosecond offsets; this is a plan-wording mismatch
- No incident, skewed record, or monotonic-reading consumer is cited

Message: box-000732-74bd7153
