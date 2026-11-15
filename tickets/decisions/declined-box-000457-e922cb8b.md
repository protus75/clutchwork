---
id: declined-box-000457-e922cb8b
kind: declined
link: box-000457-e922cb8b
reopen_after_days: 14
---
During Check for provider-failure-single-mapper, the integration test tests/integration/test_serve_dispatch.py::test_kill_aborts_requested_retro failed once and then passed on rerun. The report includes no assertion, traceback, captured output or suspected cause, and provider-failure-single-mapper has since merged.

A single fail-then-pass with no failure output does not show a reproducible runtime defect, and it does not point to one bounded repair. The ticket it touched has already merged, so the flake blocks no current work. Registry records 000359 and 000449-000451 declined the same kind of evidence-free flake report. Reopen when this test fails again with a captured traceback or assertion, or when flake detection shows it recurring often enough to block merges. With that evidence a ticket could name the cause and a measurable fix, such as zero failures over N repeated runs.

- message.class=failure_report, stage=check, outcome=gate_failed, report=null: no assertion, traceback or output attached
- summary says the test 'failed then passed' on rerun, which is a single intermittent occurrence
- provider-failure-single-mapper is in the merged set, so the failing run is no longer blocked
- declined-box-000359-7e4514be, declined-box-000449-ab280eb9, declined-box-000450-dc7224af and declined-box-000451-2cf9a4bd declined the same pattern of flaky reruns with no output
- no open ticket targets test_serve_dispatch.py kill/retro timing

Message: box-000457-e922cb8b
