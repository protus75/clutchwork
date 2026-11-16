---
id: declined-box-000498-e1a544f2
kind: declined
link: box-000498-e1a544f2
reopen_after_days: 30
---
The suggestion is to enforce the unit-test disk rule mechanically. `clutch/testguard.py` would refuse `builtins.open`/`Path.open` outside a test's `tmp_path` and the import paths, after six `tests/unit/` files that read repo files move to `tests/integration/`. Today `_guards` patches only process calls (subprocess, os.system, posix_spawn/posix_spawnp) and socket calls, so nothing stops a unit test from reading a repo file or writing outside `tmp_path`.

Declined. The gap in the guard is real, but no current harm is shown, and the fix would not fit in one buildable ticket. (1) No reported run shows a unit test touching repo disk that got past every check and caused a failure. The approve-then-fail incidents (drain-loop-prompt, vscode-help; box-000441/000442) came from the rule's copies disagreeing. Merged requisition-review-unit-disk-read and unit-criteria-disk-snag cover them, and the confirmed ticket unit-test-io-rule-one-home makes every copy agree. (2) The owner chose review over a guard on purpose: unit-test-io-rule-one-home rules out `clutch/testguard.py` changes and any engine guard for the disk rule, and its guide text says reviewers check the disk part. (3) The proposed scope is not bounded. Moving `tests/unit/test_specs.py` and `tests/unit/test_host_authoring.py` breaks the fences and Context paths of more than 20 open tickets that name them, and patching `open` across the whole covgate/xdist unit run risks blocking pytest's and coverage's own file access. That is a large, uncertain hardening change, not a repair of a harmful behavior. Reopen if, after unit-test-io-rule-one-home merges, a named run shows a `tests/unit/` test reading a repo file or writing outside `tmp_path` that passed requisition review, Check and Review and then caused a failure, a flaky result or a wasted attempt.

- clutch/testguard.py:50-60 `_guards` patches only subprocess.Popen._execute_child, os.system, os.posix_spawn/posix_spawnp, socket.connect/connect_ex/bind and socket.getaddrinfo. Nothing on disk, as the message says.
- tickets/unit-test-io-rule-one-home/ticket.md Scope out: '`clutch/testguard.py` stays unchanged... No engine lint, gate, or guard code is added for the disk rule'. Its Definition of rejected forbids adding one, and its guide text says 'reviewers check the disk part'.
- The same ticket keeps the existing repo-reading unit files in place: 'Existing `tests/unit/` files that already read repo files (for example `tests/unit/test_specs.py`) stay where they are.'
- Merged requisition-review-unit-disk-read and unit-criteria-disk-snag already snag unit-test repo reads and writes outside `tmp_path` at requisition review. This suggestion cites no incident after they merged.
- Open tickets including diagnose-spec-*, implement-spec-*, requisition-review-*, spec-paved-road-no-shim, gemini-provider, install-docs-name-clutchwork, release-publish, roadmap-* and upstream-issue-verb name `tests/unit/test_specs.py` or the other files to be moved. A move would invalidate their fences.

Message: box-000498-e1a544f2
