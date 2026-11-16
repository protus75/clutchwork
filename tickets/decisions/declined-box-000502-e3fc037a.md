---
id: declined-box-000502-e3fc037a
kind: declined
link: box-000502-e3fc037a
reopen_after_days: 14
---
The note asks for a code change so that the review-baseline GO no longer needs an operator's `--record-go --approve-author-graph` judgment and is instead set from an AI label panel whose model family differs from the judge's. Its argument is that while the baseline is not GO, every Author draft waits for a person's confirm. It also says `roadmap_row` drafts hit the same wall. The request follows the owner's 2026-11-16 'no human in the loop' decision.

This asks to change code to match a policy. It does not show any current harm. (1) The decision is not on main yet. It exists only in the confirmed but unmerged ticket roadmap-no-human-gates. That ticket's Scope out keeps the operator `--record-go` approval in `eval/harness.py` because it is code, and sends code changes to the Suggestion Box. Record 000501 declined a request of the same shape for the same reason. (2) The draft wait it describes already has a release that needs no GO. Driver open decision 5 has the supervising agent loop release Author drafts by running the Recommendation from `clutch prompt drafts`, and that verb exists. The one thing blocking that loop is CORE_TEMPLATE's confirm/reject rule, which is filed separately as box-000508. (3) The `roadmap_row` half is already covered. Open ticket roadmap-row-message makes `roadmap_row` start `confirmed` under a NO_GO or absent baseline. (4) The rest cannot be built as one bounded ticket. The fixture expectations in the review baseline already come from a different-family author. The only human step left is the Author-graph judgment, and no plan says who sits on the AI panel that would replace it, what it labels, or what agreement threshold applies. Under decision (d), an AI design panel has to settle that before anyone writes a ticket. The note also cites no run where a held draft caused harm. Reopen when roadmap-no-human-gates has merged and either (a) a recorded AI design panel has specified the Author-graph label panel (its members, the family rule, the labelled artifact and the GO threshold), or (b) a run shows an Author draft that the `clutch prompt drafts` release path could not release because the baseline was not GO. Refile with that record or run as evidence.

- eval/harness.py:270-279 `_go_report` raises unless `approve_author_graph is True` ('GO requires affirmative operator Author-graph judgment'). It also checks catch >= 0.85, false snag <= 0.15 and identity match.
- eval/harness.py:282-292 `record_go` journals the GO signal only after `_go_report` passes, and eval/harness.py:521-522 exposes `--record-go` and `--approve-author-graph` as CLI flags.
- docs/how-clutch-works.md:651-654 lists 'the review baseline is not GO' as one draft condition among several. docs/how-clutch-works.md:677-679 says the baseline gates Author starting state only.
- .clutch/state/journal/000001-20261005.jsonl has the only `review_baseline` verdict signal, and it is NO_GO. No GO has been recorded, so Author drafts start `draft` as documented.
- clutch/__main__.py:513-524 implements `clutch prompt drafts`, the release path that driver open decision 5 assigns to the supervising agent loop.
- tickets/roadmap-no-human-gates/ticket.md (confirmed, not merged), Scope out: 'The review baseline's operator `--record-go` approval in `eval/harness.py` is code and also stays'. Code changes go to the Suggestion Box, and the CORE_TEMPLATE confirm/reject change is filed as box-000508.
- tickets/roadmap-row-message/ticket.md:51,57 (open): `roadmap_row` starts `confirmed` under a NO_GO or absent baseline because `policy.start_state` exempts it from the `not go` condition.
- docs/roadmap.md:250, §5 decision 13, requires only that the judge and the generator come from different families. No doc specifies a label panel for the review-baseline Author-graph judgment.
- Decision record declined-box-000501-39826928 declined a parallel 'owner decided 2026-11-16, needs code ticket' request, because the decision is not yet on main and no harm was shown.

Message: box-000502-e3fc037a
