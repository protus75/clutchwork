---
id: declined-box-000798-7dfd22ee
kind: declined
link: box-000798-7dfd22ee
reopen_after_days: 30
---
The `prompt` row in the run guide `clutch/docs/host-running.md` says the verb renders operator prompts "without writing state". Since snapshot-from-duckdb-cache, `clutch prompt drafts` can create the DuckDB journal cache. That cache is derived data that can be rebuilt from the journal, so the sentence is now slightly loose.

This is a mismatch in how the guide describes the verb, not wrong runtime behavior. The DuckDB cache is a projection rebuilt from the JSONL journal. It is not engine state that the journal, tickets or box rely on as a source of truth. Writing it changes no ticket, journal record, lock or verdict. The message names no failure: no lock conflict with a running drain, no corrupted cache, and no wrong operator decision caused by the wording. The fix is a one-line doc edit that is cheap to fold into the next ticket that touches `clutch/docs/host-running.md` or the cache. Reopen if `prompt drafts` writing the cache is shown to cause a real fault, such as contention with a drain or serve that holds the writer lock, a stale or corrupt cache read by another verb, or a failure on a read-only checkout.

- clutch/docs/host-running.md line 22: the `prompt` verb row says it renders prompts "without writing state".
- The message comes from the snapshot-from-duckdb-cache Implement run (premise_failed). It reports a documentation mismatch only and gives no failing run.
- journal-duckdb-cache (merged) made the DuckDB cache derived data that can be rebuilt from the journal, not a source of truth.

Message: box-000798-7dfd22ee
