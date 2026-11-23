---
id: tombstone-box-000853-aaa6f5a9
kind: tombstone
link: meta-schema-and-refresh-r2
reopen_after_days: 30
---
The note asks for a new ticket to replace the rejected meta-schema-and-refresh (roadmap row 69, annotations plan ticket 1). The replacement would carry the same design: clutch/meta.py, the Meta.paths config, and the `clutch meta refresh` and `meta check` verbs. Its text would give one consistent count for the meta block, a schema version line plus six keys (kind, purpose, relates, owner, verified, hash), in every section. The note also proposes a cause fix: ticket review would check every key-count phrase against the block example.

The replacement the note asks for has already merged as `meta-schema-and-refresh-r2`. The merged stems also include later meta work built on it: meta-drift-lint, meta-fill-surface, meta-refresh-commit-lock, meta-context-ship-gate and meta-annotate-*. So the main request duplicates merged work. The cause-fix half asks ticket review to catch text that contradicts itself, such as a key count that does not match the block example. The merged ticket `review-internal-contradictions` already covers that class. The note shows no current harmful behavior beyond the original ticket's wording, which the merged r2 ticket replaced. Reopen if a new ticket fails review or Implement because its count text contradicts its own example after review-internal-contradictions.

- Merged stems list includes meta-schema-and-refresh-r2, the replacement for the rejected meta-schema-and-refresh
- Merged stems include follow-on meta work: meta-drift-lint, meta-fill-surface, meta-refresh-commit-lock, meta-context-ship-gate, meta-annotate-*
- Merged stems include review-internal-contradictions, which covers ticket text that contradicts itself
- The message itself says the first attempt's implementation passed 36 tests and only the ticket text was inconsistent

Message: box-000853-aaa6f5a9
