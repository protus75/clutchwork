---
id: tombstone-box-000442-6f3ce553
kind: tombstone
link: requisition-review-unit-disk-read
reopen_after_days: 30
---
A retro finding says requisition review approved drain-loop-prompt and vscode-help even though their acceptance criteria made tests/unit tests read real repo files (chupa/specs/ask templates, vscode-chupa/package.json, docs). Both tickets then hit premise_failed at Implement and ended in the Reject queue. It asks for a requisition_review snag on unit-test disk, process or network I/O. When the lines sit in a floored file, it wants a paved road through an in-fence seam rather than a plain move to integration. It also asks for a matching diagnose.md rule for re-scope lessons.

Open ticket requisition-review-unit-disk-read already covers this gap. It cites the same two incidents (drain-loop-prompt and vscode-help on 2026-11-13, both premise_failed, both Reject-queued). It adds the same requisition_review.md Task bullet that snags a tests/unit test made to read a named repo file. It also already counts a unit test that reaches the file through an injected seam or fake as not a hit, which is the seam escape this finding asks for. The other refinements are a floored-file seam requirement on the paved road and a diagnose.md lesson rule. Both extend the same defect and need no separate ticket. The coverage-floor side is already handled by the merged requisition-review-unit-floor rule, which raised coverage-floor-lines-unrun as designed. Reopen if requisition-review-unit-disk-read merges and a later retro still shows a re-scoped ticket stuck between the unit-disk snag and the coverage-floor snag.

- tickets/requisition-review-unit-disk-read/ticket.md Goal cites drain-loop-prompt (tests/unit/test_ask_drain_loop.py rendering chupa/specs/ask) and vscode-help (tests/unit/test_help.py reading vscode-chupa/package.json and docs), both premise_failed and Reject-queued
- tickets/requisition-review-unit-disk-read/ticket.md Scope in adds a requisition_review.md Task bullet that snags a tests/unit test made to read a named repo file
- tickets/requisition-review-unit-disk-read/ticket.md guard clause: a unit test that reaches a repo file only through an injected seam or fake is not a hit
- requisition-review-unit-floor is merged and owns the coverage-floor-lines-unrun snag the finding reports after re-scope

Message: box-000442-6f3ce553
