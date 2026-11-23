---
id: declined-box-001053-87d6b124
kind: declined
link: box-001053-87d6b124
reopen_after_days: 30
---
The suggestion is to stop drain and serve from deciding separately when an unforced retro check runs. Today drain checks on every loop pass and serve checks after a ticket reaches a terminal state, and the two rules drifted apart. The proposal is one shared due-check in clutch/retro.py that both call, as the cause fix behind the instance ticket drain-retro-check-once-per-settle.

There is no current harmful behavior left to fix. The instance ticket drain-retro-check-once-per-settle is in the merged set. Its Goal makes drain's unforced check follow serve's rule: check once when the process starts, then only after the count of terminal transitions grows. Once it landed, both engines schedule the check the same way, and the deciding logic in clutch/retro.py (`due_trigger`/`select_trigger`) already has one owner, used by Retro.__call__ and status. What remains is two small, matching settle checks, one in drain.py and one in serve.py. Merging them into one predicate is a refactor and speculative prevention, not a fix for reachable incorrect runtime behavior. Reopen if drain and serve diverge again on when an unforced retro check runs, for example one checks without a new settle or skips a check after one, and engine.log shows it costing drain or serve time or missing a due retro.

- Merged stem drain-retro-check-once-per-settle: its Goal makes drain's unforced retro check run on the first between-tickets point of each process, then only when the terminal-transition count grows, which matches serve.
- The same ticket's Goal records that serve already checks only after a transition in TERMINAL_STATES (`clutch/serve.py` check_retro).
- clutch/retro.py:209 `due_trigger` is the single shared decision on whether a retro is due; it is called from clutch/retro.py:436 and clutch/status.py:51.
- Merged stems retro-due-one-owner and retro-check-once already consolidated how a due retro is decided and checked.
- The message describes no current divergence; the drift it cites is the one the merged instance ticket repaired.

Message: box-001053-87d6b124
