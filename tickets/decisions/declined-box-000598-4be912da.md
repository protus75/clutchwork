---
id: declined-box-000598-4be912da
kind: declined
link: box-000598-4be912da
reopen_after_days: 14
---
The roadmap-held-row-refile ticket's Check stage reported that the whole integration suite (`uv run python -m pytest tests/integration ... -n auto`) also failed on merge base d906284a, so the outcome was base_red. The report does not name the failing test or include any output.

No current failure is left to repair. The report names no failing test, assertion or traceback. Its origin ticket, roadmap-held-row-refile, is now merged, and its committed checks.json shows a green final Check with 0 failed and base_red false. The base-red failure in the integration suite at the same time was most likely tests/integration/test_closed_sets_single_owner.py::test_follow_up_row, which expected roadmap row 19 to stay unstruck after the driver struck it. Merged ticket closed-sets-follow-up-row-struck fixed that test. The report cannot be tied to that test for certain, so it is declined, not tombstoned. Reopen if the integration suite is red on current main and the report includes the failing test id and its output.

- tickets/roadmap-held-row-refile/checks.json: failed 0, base_red false (roadmap-held-row-refile is in the merged set)
- tickets/closed-sets-follow-up-row-struck/evidence/failure.txt: test_follow_up_row failed at tests/integration/test_closed_sets_single_owner.py:50 on the shared base
- Record tombstone-box-000597-f924394e links the same test_follow_up_row base failure to merged ticket closed-sets-follow-up-row-struck
- The message carries no failing test id, traceback or captured output (report: null)

Message: box-000598-4be912da
