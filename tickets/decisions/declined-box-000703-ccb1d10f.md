---
id: declined-box-000703-ccb1d10f
kind: declined
link: box-000703-ccb1d10f
reopen_after_days: 30
---
During the plan-drain-author-in-parallel Implement run, the agent saw the host-loop integration fixture sometimes write journal timestamps out of order. The affected tests still passed on the base commit, when run alone, and in the final full suite run. The report gives no failing test, no assertion or traceback, no example timestamps and no suspected cause.

The report shows no harmful behavior: every affected test passed in each of the three runs it describes. It does not name the test, the out-of-order events or the code that wrote them, so no ticket can be bounded to a cause or given a measurable result. Earlier host-loop flake reports with no output were declined for the same reason (box-000449, box-000450, box-000451). Box-000395 notes that the host-loop FixtureLoop runs on the real wall clock (datetime.now(UTC)), which might explain out-of-order timestamps, but nothing here links that to a failed run or a wrong engine decision. Reopen if a run fails or makes a wrong decision because of out-of-order journal timestamps, and the report includes the failing test, the out-of-order event pair and the code that wrote them.

- The message's outcome is ok, and it says the affected tests passed on the base commit, in isolation and in the final full run.
- No test name, assertion, traceback or timestamp sample is given.
- Host-loop flakes reported without output were declined as box-000449, box-000450 and box-000451.
- Box-000395 records that the host-loop FixtureLoop uses the real wall clock (datetime.now(UTC)) and real sleeps.

Message: box-000703-ccb1d10f
