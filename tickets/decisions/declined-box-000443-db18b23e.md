---
id: declined-box-000443-db18b23e
kind: declined
link: box-000443-db18b23e
reopen_after_days: 14
---
On 2026-11-13, codex quit Implement without producing a diff on 7 of 15 prompts that rendered at 80 KB or more, and on none of 16 smaller prompts. Each quit was an `incomplete` reply followed by an admitted `premise_failed`. The note suggests a per-provider render ceiling, a size warning when a ticket is authored, or sending large renders to a higher tier.

The harm in this report is already covered. The open P0 ticket `implement-incomplete-outcome` cites the same seven quits on 2026-11-13 across the same three stems. It makes `incomplete` a real outcome that counts toward attempts, draws no `premise_bounce`, and is offered again as a `retry`. Once it lands, a quit costs one retry and no longer parks the ticket in the Reject queue. The idea that render size causes the quits is not shown. All 7 quits come from only 3 tickets, so prompt size cannot be separated from how hard those tickets are. `menu-table-run-review-admission` quit at a large size and then succeeded on a plain retry, and it is now merged, so size alone does not decide the outcome. Large failures already have a way up the ladder: a Diagnose `escalate` verdict, or the same failure reason three times in a row. The note also offers three different fixes instead of one buildable ticket. Reopen if, after `implement-incomplete-outcome` merges, `incomplete` terminals still cluster on renders of 80 KB or more across at least 5 distinct tickets, with smaller renders of the same tickets succeeding, or keep using up `retry` caps where escalation does not help.

- tickets/implement-incomplete-outcome/ticket.md: Goal cites the same 2026-11-13 pattern (an `incomplete` first reply, then an admitted `premise_failed`, seven times across vscode-help, menu-mirrors-verb-admission, menu-table-run-review-admission) and fixes how it is classified and routed
- tickets/implement-incomplete-outcome/ticket.md: 'menu-table-run-review-admission then succeeded on a plain retry, so a quit is a retry case, not a ticket defect'
- menu-table-run-review-admission is in the merged set even though one of its large renders quit
- All 7 large-render quits come from only 3 stems, so size cannot be separated from ticket difficulty
- tickets/implement-incomplete-outcome/ticket.md Scope out: an existing escalation rule (a Diagnose escalate verdict, or the same reason three times) already moves the provider rung

Message: box-000443-db18b23e
