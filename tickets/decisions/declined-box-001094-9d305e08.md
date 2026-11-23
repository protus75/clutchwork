---
id: declined-box-001094-9d305e08
kind: declined
link: box-001094-9d305e08
reopen_after_days: 30
---
Ticket shared-git-fake-unit-4 deleted the `FakeGit` class from tests/unit/test_roadmap_author.py, but tests/unit/test_roadmap_accept.py imports that name and was outside the fence. Check failed with an ImportError. Diagnose then kept a factory `FakeGit` in place, the retry stayed inside the fence, and the ticket merged. The suggestion is for lint or ticket review to list every tests/ module that imports from a fenced test module, and to require each one in the fence or an explicit reason.

The incident is real and cost one Check cycle and one Diagnose call. Today nothing checks importers mechanically: requisition_review.md says not to search for importers, and lint has no importer check. But the rule as proposed would raise a finding for every importer of any fenced test module, whatever the change does to it. CLAUDE.md records that tests/integration/test_cli.py is imported by 60 test modules, so any ticket fencing a shared helper module would need dozens of fence entries or written reasons. That widens fences and makes tickets collide, which the hot-file rule exists to avoid. Lint cannot tell at authoring time which symbols a change removes, so a precise version is not a single bounded ticket. Record 000555 already declined a review-side rule that greps for importers of deleted symbols. The cost of a fence gap is being addressed by open ticket implement-fence-gap-keeps-branch, and Diagnose already found an in-fence fix here. Reopen if this miss happens again on another ticket, or if someone proposes a narrow mechanical rule: flag only importers of a symbol that Scope in names as removed or renamed from a tests/ module.

- tickets/shared-git-fake-unit-4/diagnosis.json:11 says tests/unit/test_roadmap_accept.py:29 imports FakeGit from tests.unit.test_roadmap_author, and the diff deleted that class
- tickets/shared-git-fake-unit-4/diagnosis.json:12 gives an in-fence fix: keep a `def FakeGit(repo)` factory
- shared-git-fake-unit-4 is in the merged set, so the instance is resolved
- clutch/specs/requisition_review.md:16 tells the reviewer not to search for importers
- Nothing in clutch/tickets.py lint computes importers
- CLAUDE.md hot-file rule: test_cli.py is imported by 60 test modules, so a fence-every-importer rule would be too broad
- Record declined-box-000555-0d8ce6cf declined a similar grep-importers review rule
- Open ticket implement-fence-gap-keeps-branch reduces the cost of fence-gap retries

Message: box-001094-9d305e08
