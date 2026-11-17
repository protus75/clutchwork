---
id: tombstone-box-000601-4e2f0dc5
kind: tombstone
link: closed-sets-follow-up-row-struck
reopen_after_days: 30
---
A roadmap-status-stuck-rows Implement run said that tests/integration/test_closed_sets_single_owner.py::test_follow_up_row failed on its base commit. The test expected a roadmap row to be unstruck, but the driver had already struck that row.

This is the same failure that registry record tombstone-box-000597-f924394e already covers. Merged ticket closed-sets-follow-up-row-struck fixed it. On current main the test no longer asserts that row 19 is unstruck. It checks only that row 19's stem is closed-sets-single-owner, and it checks the follow-up row's fields. Reopen if the test fails again on current main.

- Merged stems include closed-sets-follow-up-row-struck.
- Registry record tombstone-box-000597-f924394e reports the same test failing for the same reason, a struck row 19, and links it to closed-sets-follow-up-row-struck.
- tests/integration/test_closed_sets_single_owner.py:55 now asserts only that row 19's stem is closed-sets-single-owner. It no longer asserts that the row is unstruck.

Message: box-000601-4e2f0dc5
