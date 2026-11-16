---
id: declined-box-000560-b39d4505
kind: declined
link: box-000560-b39d4505
reopen_after_days: 30
---
Roadmap row 21 (test-fakes-and-conftest, a P2 test-harness chore) is held by the driver's declined-row rule after Author draft box-000559 was declined. The draft claimed a shared fakes.until with one `await asyncio.sleep(0)` would keep serve_rig's pacing. But tests/integration/serve_rig.py::until yields through test_scheduler.turn(), which takes two event-loop iterations per turn. The note asks for row 21's Content in docs/roadmap.md to be reworded so the shared until keeps the two-iteration turn, or so serve_rig's until is left in place.

The engine works as designed here. A declined roadmap row is not re-filed until its Content changes, and that hold is the intended release path. The held row is a test-only refactor that moves fakes into tests/conftest.py and tests/fakes.py. No ticket or roadmap row depends on test-fakes-and-conftest; it appears only in docs/roadmap.md lines 120 and 321, and plan and ticket prose mention it without a dependency. So leaving the row stalled causes no reachable incorrect runtime behavior. The fix the note asks for is a wording change to a planning document. Under the admission bar, that is a doc or cleanup change for a test-only row and does not justify authoring a ticket. The open ticket closed-sets-single-owner-refile already edits docs/roadmap.md for row 19. The operator can reword row 21 in a docs edit they choose, which releases the hold without a triage-authored ticket. Reopen if a later roadmap row or ticket lists test-fakes-and-conftest under Depends on, which would make the stall block release work. Also reopen if the declined-row hold stops releasing after row 21's Content has been reworded.

- docs/roadmap.md:321 row 21 Content still says 'one `until`' and 'serve_rig.py ... migrate', with no statement about preserving the two-iteration turn
- tests/integration/serve_rig.py:27-35 `until` awaits turn(), defined at tests/integration/test_scheduler.py:41
- decision registry declined-box-000559-eb6901f3: Author could not produce a ticket for row 21
- No ticket.md or roadmap row lists test-fakes-and-conftest under Depends on; the only references are docs/roadmap.md:120 and 321, docs/parallel-tickets-plan.md:121, and prose in tickets/roadmap-plan-corrections and tickets/contention-authoring-rules
- Row 21 is kind chore, priority P2, and test-harness only (tests/conftest.py, tests/fakes.py, serve_rig.py migration)

Message: box-000560-b39d4505
