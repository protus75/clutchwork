---
id: tombstone-box-001096-2ca2d238
kind: tombstone
link: requisition-review-collection-policy
reopen_after_days: 14
---
The note asks ticket lint or review to refuse two kinds of test references that cannot prove anything. The first is a Verification command, acceptance criterion or Regression carry that names a tests/integration file listed in DISK_IO_SKIP, so the test is skipped and passes without checking anything. The second is a new integration test that needs real I/O but is not listed in REAL_IO_TESTS, so the I/O guard blocks it. It cites serve-contains-dispatch-exception and check-rerun-failed-only, which both ended premise_failed for this reason. It also says some carried reproducers, such as tests/regress_drain_containment.py, now run skipped tests and pass without checking anything.

The open ticket requisition-review-collection-policy already covers this defect class. When it is done, the requisition review spec tells the reviewer to raise a snag for any criterion that names tests in a DISK_IO_SKIP file and for any required new test that the REAL_IO_TESTS guard would block. It cites the same incidents, serve-contains-dispatch-exception and the skip-only pass on serve-flaky-tests-deterministic. The extra wish for a lint rule, as opposed to a review snag, describes another way to enforce the same rule, not a separate runtime defect. Reopen if, after that ticket merges, a ticket that names a skipped or guard-blocked integration test still gets past review and fails at Implement, or if a carried reproducer that passes only through skips is shown to have let a regression merge.

- The open ticket requisition-review-collection-policy names DISK_IO_SKIP in tests/integration/conftest.py and IntegrationIOBlocked/REAL_IO_TESTS in clutch/ioguard.py, and its paved road is a requisition review snag.
- That ticket cites serve-contains-dispatch-exception (serve_rig real repo blocked outside REAL_IO_TESTS) and serve-flaky-tests-deterministic (8 passed, 49 skipped).
- The message's cost evidence (premise_failed bounces at Implement) is the same harm the open ticket targets.

Message: box-001096-2ca2d238
