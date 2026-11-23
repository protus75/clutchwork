---
id: tombstone-box-000858-62f027b5
kind: tombstone
link: review-panel-r2
reopen_after_days: 30
---
This session note proposes replacing the rejected review-panel ticket (roadmap row 67) with two tickets. The first would add a member-scoped effect key and update every six-part key reader. The second would make the review, requisition review, diagnosis and triage call sites use the panel combiners, with a full tie order. It also asks that author-stage review check that the readers of a new key shape are fenced. That split has already merged. review-panel-r2 delivered member keys, and the review-panel-stage-use family delivered the stage use and tie orders.

Merged ticket review-panel-r2 is the replacement for the rejected review-panel stem. It builds member effect keys and leaves stage use and tie order to review-panel-stage-use. It deliberately rejects a seventh `/m<k>` key part: it scopes run_seq instead as `m<k>-<run_seq>`, which keeps the key at six parts, so no reader in rework, stats, scorecard or training has to change. The stage-use half is merged as review-panel-stage-use (review), review-panel-stage-use-majority (diagnosis, with the panel tie orders), review-panel-stage-use-requisition and review-panel-stage-use-triage. Panel combiners, scorecard and routing config are also merged. The proposed cause fix about fencing the readers of a new key shape has no failure behind it, because the merged design never changed the key shape. Reopen within 30 days only if a six-part key reader is shown to misparse an `m<k>-<run_seq>` member key at runtime.

- tickets/review-panel-r2/ticket.md:83 sends stage use and the diagnosis and triage tie orders to review-panel-stage-use
- tickets/review-panel-r2/ticket.md:121 rejects a seventh `/m<k>` key part and any edit to the rework, stats, scorecard or training parsers
- tickets/review-panel-stage-use/ticket.md:54 says member keys are `llm/<stem>/m<k>-<run_seq>/review/...`, six parts, so every six-part reader accepts them
- tickets/review-panel-stage-use-majority/ticket.md:68 contains a 'Panel tie orders' section
- Merged stems include review-panel-r2, review-panel-stage-use, review-panel-stage-use-majority, review-panel-stage-use-requisition, review-panel-stage-use-triage, panel-combiners and panel-scorecard

Message: box-000858-62f027b5
