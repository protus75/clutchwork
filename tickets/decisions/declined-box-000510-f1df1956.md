---
id: declined-box-000510-f1df1956
kind: declined
link: box-000510-f1df1956
reopen_after_days: 30
---
The message asks for a runner rule or audit check that refuses any Effect intent for a stem after that run's terminal is journaled. The case it guards against: an Effect such as an LLM call, a ticket-plane commit or a lift starts after the terminal and then fails. `reconcile.orphans` clears a stem's open intents only at a terminal transition, so the leftover intent makes the stem look like an open run. The next lock-taking verb then reaps it as `abandoned`, which is a second terminal for one run, and `audit_journal` flags `one_terminal_per_run`. The only time this happened was in an unmerged supervisor-rework prototype at 4d4cb7b5.

Merged code has no path that starts an Effect after a terminal, so there is nothing on main to fix. In `clutch/runner.py::failure_terminal`, harvest, diagnosis and `apply_rework` all run before the terminal is appended at line 434. The only work after that line is the split path's `reject_ticket` and the worktree removal. `reject_ticket` commits through `git.commit` directly, not through `effects.run`, so it never opens an intent that `orphans` would see, and the auditor lets `rejected` through. The only code that triggered the bug is the prototype, and the open ticket `supervisor-rework` already rules it out. Its Goal says every supervisor effect (Rework calls, publication, the `rework.md` lift) runs before the terminal and names this exact reap. Its acceptance criterion 2 rules out effects after the terminal, and its Definition of rejected refuses any supervisor effect after the terminal or two terminals in one run. A general audit check, with nothing on main that writes post-terminal intents, would be hardening against a risk that has not happened. Decision 000278 already declined an auditor and reconcile mismatch on intent-only reaps. Reopen if merged code or an open ticket's design starts an Effect for a stem after that run's terminal outside `supervisor-rework`, or if a real journal shows a reconcile `abandoned` reap that follows a terminal already written for the same run.

- clutch/reconcile.py:17-38: `orphans` drops a stem's intents only on a TERMINAL_STATES transition, so an intent left open after a terminal makes the stem an orphan
- clutch/runner.py:434: `failure_terminal` appends the terminal after harvest (line 371), diagnosis (lines 265, 293) and apply_rework (line 305)
- clutch/runner.py:435-440 and 604-616: after the terminal, only `reject_ticket` (direct `git.commit`, no `effects.run` intent) and `worktree_remove` run
- clutch/audit.py:73-97: `one_terminal_per_run` lets `rejected` through, so the split path's `to: rejected` is not a violation
- tickets/supervisor-rework/ticket.md:48: 'Every effect of the step ... runs before the terminal is journaled' names the prototype's reap of the stem as `abandoned` as the reason
- tickets/supervisor-rework/ticket.md:104,143: the acceptance criterion rules out effects after the terminal, and the Definition of rejected refuses any supervisor effect after the terminal or two terminals in one run
- tickets/decisions/declined-box-000278-70140c4c.md: an earlier auditor and reconcile mismatch on intent-only reaps was declined

Message: box-000510-f1df1956
