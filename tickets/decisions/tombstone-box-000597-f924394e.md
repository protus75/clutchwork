---
id: tombstone-box-000597-f924394e
kind: tombstone
link: closed-sets-follow-up-row-struck
reopen_after_days: 30
---
An Implement run found that `tests/integration/test_closed_sets_single_owner.py::test_follow_up_row` failed. The test expected roadmap row 19 to stay unstruck after the driver had struck it, and the run saw the same failure on the base commit.

This is the same failure that the merged ticket closed-sets-follow-up-row-struck fixed. That ticket's criterion requires `./dev.py test tests/integration/test_closed_sets_single_owner.py` to exit 0 with row 19 struck, as it is on main. On current main, `test_follow_up_row` no longer checks whether row 19 is unstruck. It only checks that row 19's stem is closed-sets-single-owner. Reopen if the test fails again on current main.

- tickets/closed-sets-follow-up-row-struck/ticket.md acceptance criterion 1: test file exits 0 with row 19 struck as on main
- closed-sets-follow-up-row-struck is in the merged stems list
- tests/integration/test_closed_sets_single_owner.py:55 now checks only the stem of row 19, not whether it is struck

Message: box-000597-f924394e
