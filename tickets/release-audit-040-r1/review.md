# Review: snag

The 0.5.0 audit row (155, unused number), the unchecked-clause prose line and the Status refresh are correct, but the audit removes or narrows three sections 2-4 items that merged work did not fully fix, which breaks criterion 3.

## Findings

- [acceptance] docs/roadmap.md:61 The §2.2 'Settled and retired states' row was deleted, but the duplication is still there. `clutch/tickets.py:813` still spells the literal `{"merged", "already_satisfied", "rejected"}` instead of using `status.CLOSED`, and `clutch/stats.py:149` hand-lists the same states. The `closed-sets-remaining` ticket lists 'the `tickets.py` literal' in its Out scope. No merged change fixed this item, so the row cannot be removed. (do instead: Put the row back. Restate its homes as they are at the base commit (for example the `tickets.py:813` literal and the `stats.py:149` tuple, with owner `status.CLOSED`) and mark it "(recurred in 0.4.0)".)
- [acceptance] docs/roadmap.md:131 The rewritten §3.5 'No engine caller' item leaves out `Git.init` (`clutch/git.py:58`) and `audit.audit` (`clutch/audit.py:36`). Both still exist, and neither has an engine caller: no module in `clutch/` calls `.init(`, and `audit_journal` is called only from inside `audit.py`. The item now says `engine-callerless-code` removed the other unused paths, which is false for these two. (do instead: Add `Git.init` and `audit.audit` (with its wrapper `audit_journal`) back to the still-callerless list in that item. Re-check each originally listed symbol at the base commit and drop only the ones that were actually deleted or now have an engine caller.)
- [acceptance] docs/roadmap.md:93 §2.5 was replaced with one sentence that has no "recurred in 0.4.0" mark. `rule-restatements-single-home` (row 126) fixed only the document restatements in `host-contract.md`, `how-clutch-works.md` and `host-authoring.md`. The conduct-file restatements in the original item are still present: for example, read-before-write and file-second-problems appear in `hostfiles.py` CORE_TEMPLATE, the managed block of `CLAUDE.md`, and `CLAUDE.md`/`AGENTS.md` section A. The rewrite drops that still-true part, and the changed item has neither an unchanged description nor the required mark. (do instead: Keep §2.5 as an item that names the restatements still present at the base commit (CORE_TEMPLATE vs. `CLAUDE.md`/`AGENTS.md` section A, and specs where models need them). Remove only the document restatements that row 126 fixed, and add "(recurred in 0.4.0)".)

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "aae8dd5ee69e683b7b0f6edab032616b71ff0e38",
  "stem": "release-audit-040-r1",
  "reviewed_sha": "aae8dd5ee69e683b7b0f6edab032616b71ff0e38",
  "summary": "The 0.5.0 audit row (155, unused number), the unchecked-clause prose line and the Status refresh are correct, but the audit removes or narrows three sections 2-4 items that merged work did not fully fix, which breaks criterion 3.",
  "findings": [
    {
      "code": "acceptance",
      "path": "docs/roadmap.md",
      "line": 61,
      "message": "The §2.2 'Settled and retired states' row was deleted, but the duplication is still there. `clutch/tickets.py:813` still spells the literal `{\"merged\", \"already_satisfied\", \"rejected\"}` instead of using `status.CLOSED`, and `clutch/stats.py:149` hand-lists the same states. The `closed-sets-remaining` ticket lists 'the `tickets.py` literal' in its Out scope. No merged change fixed this item, so the row cannot be removed.",
      "paved_road": "Put the row back. Restate its homes as they are at the base commit (for example the `tickets.py:813` literal and the `stats.py:149` tuple, with owner `status.CLOSED`) and mark it \"(recurred in 0.4.0)\".",
      "kind": null,
      "unit": null
    },
    {
      "code": "acceptance",
      "path": "docs/roadmap.md",
      "line": 131,
      "message": "The rewritten §3.5 'No engine caller' item leaves out `Git.init` (`clutch/git.py:58`) and `audit.audit` (`clutch/audit.py:36`). Both still exist, and neither has an engine caller: no module in `clutch/` calls `.init(`, and `audit_journal` is called only from inside `audit.py`. The item now says `engine-callerless-code` removed the other unused paths, which is false for these two.",
      "paved_road": "Add `Git.init` and `audit.audit` (with its wrapper `audit_journal`) back to the still-callerless list in that item. Re-check each originally listed symbol at the base commit and drop only the ones that were actually deleted or now have an engine caller.",
      "kind": null,
      "unit": null
    },
    {
      "code": "acceptance",
      "path": "docs/roadmap.md",
      "line": 93,
      "message": "§2.5 was replaced with one sentence that has no \"recurred in 0.4.0\" mark. `rule-restatements-single-home` (row 126) fixed only the document restatements in `host-contract.md`, `how-clutch-works.md` and `host-authoring.md`. The conduct-file restatements in the original item are still present: for example, read-before-write and file-second-problems appear in `hostfiles.py` CORE_TEMPLATE, the managed block of `CLAUDE.md`, and `CLAUDE.md`/`AGENTS.md` section A. The rewrite drops that still-true part, and the changed item has neither an unchanged description nor the required mark.",
      "paved_road": "Keep §2.5 as an item that names the restatements still present at the base commit (CORE_TEMPLATE vs. `CLAUDE.md`/`AGENTS.md` section A, and specs where models need them). Remove only the document restatements that row 126 fixed, and add \"(recurred in 0.4.0)\".",
      "kind": null,
      "unit": null
    }
  ],
  "spec_version": "1.7",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "snag"
}
```
