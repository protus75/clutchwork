---
id: tombstone-box-000851-758c6f96
kind: tombstone
link: lint-refuses-two-dot-git-diff-main
reopen_after_days: 30
---
A ticket's criterion or Verification command used `git diff --name-only main` (two dots, or a bare `main`). That compares the branch with main as it is now, not with the attempt's base. Implement attempt 0 of visual-baseline-fixtures started from b9caf305 while main had moved to 9f21ef9b. Two ticket files outside the fence therefore already differed, and the attempt ended premise_failed after finishing its in-fence work. The proposal is to flag this form during authoring and require the merge-base form `main...HEAD`.

The open ticket lint-refuses-two-dot-git-diff-main already covers this same defect. It cites the same visual-baseline-fixtures attempt 0 premise_failed on 2026-11-19, explains the same failure (another ticket merges after the attempt's base, so an in-fence-only criterion fails), and lists the other tickets that use the form. It enforces the paved road at authoring time through `clutch ticket lint`, which runs before requisition review. Adding a requisition_review.md snag on top would be a second enforcement path for one class fix. Reopen if that ticket merges and a two-dot or bare-main diff criterion still reaches Implement.

- The message names visual-baseline-fixtures attempt 0: base b9caf305, main at 9f21ef9b, criterion 5 `git diff --name-only main`, ended premise_failed
- The open ticket lint-refuses-two-dot-git-diff-main describes the same command form, the same incident, and the same other tickets that use it
- Merged ticket visual-baseline-fixtures was reworded to the merge-base form after Diagnose's lesson, so that instance is already fixed

Message: box-000851-758c6f96
