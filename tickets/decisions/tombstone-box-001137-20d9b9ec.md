---
id: tombstone-box-001137-20d9b9ec
kind: tombstone
link: requisition-review-collection-policy
reopen_after_days: 14
---
The retro-calibration-manual run found that its integration Verification named test files that the DISK_IO_SKIP policy skips. Those tests never ran the doctor, serve, drain and config behavior the ticket specified, so Verification passed without checking anything.

Records 001133 and 001136 have already sent this incident from the same retro-calibration-manual run to the open ticket requisition-review-collection-policy. That ticket covers this exact problem: a ticket names integration tests that DISK_IO_SKIP skips or IntegrationIOBlocked blocks, so its criteria pass only as skips. Once it is done, requisition review raises a snag before Implement runs. This message repeats the same gap in different words. Reopen if that ticket merges and a later ticket still gets approved with Verification that names only skipped integration files.

- The message comes from retro-calibration-manual (stage implement, outcome ok). It says the skip policy stops the specified tests from exercising doctor, serve, drain and config behavior.
- Open ticket requisition-review-collection-policy makes requisition review raise a snag when named tests sit in DISK_IO_SKIP in tests/integration/conftest.py or are blocked by IntegrationIOBlocked.
- Record tombstone-box-001133-d3050537 sent the same retro-calibration-manual DISK_IO_SKIP report to requisition-review-collection-policy.
- Record tombstone-box-001136-71491e78 did the same for the report that all 270 tests in that run were skipped on both the branch and the base commit.

Message: box-001137-20d9b9ec
