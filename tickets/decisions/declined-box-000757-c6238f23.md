---
id: declined-box-000757-c6238f23
kind: declined
link: box-000757-c6238f23
reopen_after_days: 30
---
A host session (Fungo, fit-tree work) reports that an Implement retry cleared the four findings the prior Review named and resubmitted, and the next Review then raised two more unmet requirements, costing one extra review/retry cycle. The suggestion asks the Implement retry prompt to make the agent re-check every ticket requirement before resubmitting, not only the named findings.

The current engine already asks for what this suggestion wants. `clutch/specs/implement.md` step 2 requires every attempt, retries included, to "Meet every acceptance criterion". Line 72 already says "On a retry, check every assertion this way, not only the one a finding names." On re-entry, `clutch/stages.py::prior_attempts` places the prior findings inside the Acceptance criteria section, labelled "this attempt's to clear, beside the acceptance criteria above; they are not part of the ticket", so the retry sees the full criteria list next to the findings. The report is one secondhand host incident with no run record, findings text, or journal evidence. It does not show whether the two later findings were unmet acceptance criteria that the retry ignored, or new defects that the first Review missed and that no Implement wording would have prevented. A third wording patch would rest on that unproven premise, and the repo has already declined single-incident Implement-spec wording additions (box-000313, box-000393). Reopen if a clutch retro or journal shows at least two runs where a retry's Review raised a finding citing an acceptance criterion that was already unmet at the prior Review and that the retry left untouched, with the review.md files of both attempts as evidence.

- clutch/specs/implement.md:22 'Meet every acceptance criterion with the simplest change that does.' applies on every attempt
- clutch/specs/implement.md:72 'On a retry, check every assertion this way, not only the one a finding names.'
- clutch/stages.py:597-600 prior_attempts renders findings 'beside the acceptance criteria above' and places them inside the Acceptance criteria section (_in_criteria_position)
- Message has origin=session, no stage/outcome/report and no run record; it is a single host incident with no review.md showing whether the later findings were pre-existing unmet criteria
- Precedent: box-000313 and box-000393 declined single-incident Implement-spec wording rules

Message: box-000757-c6238f23
