---
id: declined-box-000465-624173ac
kind: declined
link: box-000465-624173ac
reopen_after_days: 30
---
While implementing verdict-decisions-retire-on-resolution, the run noticed that three other fields in `clutch/status.py` `project` also keep events from the whole journal and never drop old ones: `Status.verdict_refusals`, `Status.intake` and `Status.reopens`. It suggests they may need retirement rules like the one just added for `verdict_decisions`.

Nothing here shows a harmful runtime problem today. Only `render` in `clutch/status.py` (lines 268, 276, 277) reads these three fields, and it prints them as text in `clutch status`. Neither `clutch/observe.py` snapshot nor `vscode-clutchwork/media` reads them, so the tickets view does not fill up with them the way it did with the verdict-decisions rows. `intake` and `Tombstone reopens` are history logs by design: each row records a real intake commit or an auto-reopen, and none of them claims something is still waiting for action. `verdict_refusals` is the only one that could look actionable. The report names no refusal that stayed listed after it was resolved, no operator who was misled, and no condition that would mark a refusal as resolved. The source ticket's Scope out also lists these fields only as a second problem to file, without evidence. The note itself says 'may need', so this is speculative cleanup. Reopen if someone shows a `Verdict refusals` row (or one from another of these blocks) that stays after its stem's verdict was applied and misleads an operator, or if any of these fields is added to the snapshot or the extension.

- tickets/verdict-decisions-retire-on-resolution/run.md:15 says these projections 'may need separate retirement rules' and gives no incident
- tickets/verdict-decisions-retire-on-resolution/ticket.md:43 puts verdict_refusals, intake and reopens in Scope out as a second problem, with no observed harm
- clutch/status.py:224-235 builds the three fields from the whole journal
- clutch/status.py:268,276,277: render is the only reader; a grep of clutch/**/*.py and vscode-clutchwork/media/*.js finds no snapshot or extension use
- The intake and Tombstone reopens blocks list events that happened, not items still waiting for action

Message: box-000465-624173ac
