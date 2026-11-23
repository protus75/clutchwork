---
id: tombstone-box-001033-88380fca
kind: tombstone
link: declined-box-000598-4be912da
reopen_after_days: 14
---
Check for roadmap-meta-resync ended base_red: the whole parallel integration suite run (`pytest tests/integration -p clutch.testreport ... -n auto`) also failed on merge base c6c2af7d, and the report asks for main to be fixed rather than the ticket. It names no failing test and gives no assertion, traceback or output. roadmap-meta-resync has since merged.

This is the same kind of report that records 000598, 000602 and 001013 already declined: a base_red at Check on the whole integration suite that names no failing test and has no output. The one likely cause it hints at is the known intermittent serve-admission and host-loop failures, which records 000983 and 000703 already cover. In the same run, record 001032 recorded the serve-admission precheck case failing once at Check. roadmap-meta-resync is in the merged set, so no ticket is still blocked. Reopen if a base_red report names a specific integration test that fails deterministically on main, with its assertion or traceback.

- message: class failure_report, stage check, outcome base_red, origin roadmap-meta-resync, merge base c6c2af7d, no test named, report null
- declined-box-000598-4be912da and declined-box-000602-8ec884ea: same whole-integration-suite base_red with no failing test named
- declined-box-001013-d4549bb5: same shape for merge-dirty-checkout-never-blocks
- tombstone-box-001032-61ce414b: roadmap-meta-resync Check saw a serve-admission precheck flake, linked to declined-box-000983-96a0ff93
- roadmap-meta-resync appears in the merged stems list

Message: box-001033-88380fca
