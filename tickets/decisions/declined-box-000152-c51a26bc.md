---
id: declined-box-000152-c51a26bc
kind: declined
link: box-000152-c51a26bc
reopen_after_days: 90
---
The note says the drain's self-upgrade handoff closes only `checkout.journal`, while the Driver built in `runner.bind` keeps its own second Journal over the same state dir, and nothing closes it. It proposes passing one journal through the Driver so the close covers every writer. Record 000126 already settled this: `runner.bind` replaces the Driver's journal with the checkout's journal.

This is the same issue as declined-box-000126-16b156ae, and current code already does what the note asks. `runner.bind` sets `driver.journal = checkout.journal` and builds `driver.effects` from that same handle (`clutch/runner.py:133-134`, and again at `:468-469` on the run path). So every Driver write goes through the handle the handoff closes. `Driver.from_config` does create a Journal (`clutch/driver.py:169`), but `bind` replaces it before any write. `Journal.__init__` opens no file descriptor or lock (`clutch/journal.py:146-150`), so the replaced object holds nothing and never writes. A child process cannot be affected by it, so the note shows no harm at runtime.

- clutch/runner.py:131-134 bind: driver.journal = checkout.journal; driver.effects = Effects(checkout.journal)
- clutch/runner.py:468-469 run path performs the same rebinding
- clutch/driver.py:169 from_config builds a Journal that bind overwrites before use
- clutch/journal.py:146-154 Journal.__init__ opens no fd; close() only sets _closed
- Decision declined-box-000126-16b156ae already found the Driver and checkout share one journal object
- unresolvable link: declined-box-000126-16b156ae

Message: box-000152-c51a26bc
