---
id: declined-box-000756-c97e1d39
kind: declined
link: box-000756-c97e1d39
reopen_after_days: 30
---
A roadmap-driven Author draft for boundary-contract-authoring said in its Scope out that the change must not edit the boundary plan document. It treated that plan as frozen, but only CLUTCH_PLAN.md is frozen. Merging the draft as written would have left the `## Status` section of docs/boundary-contract-plan.md saying nothing had been built. A supervising session fixed the draft by hand before it ran. The proposed class fix has three parts: the Author spec and authoring guide say that only the bootstrap plan is frozen, a ticket fences and updates the Status section of the plan its row implements, and requisition review flags a Scope out that bars a plan document the change makes false.

This is one incident, and it was fixed before Implement ran, so nothing wrong reached main. The only harm it could have caused is a stale Status section in a planning document. Stale plan documents are a documentation-truth issue, not incorrect runtime behavior. This registry has declined every report of a stale plan document left by a merged change (for example box-000526, 000530, 000594, 000621, 000627, 000646, 000656). A grep shows that `clutch/specs/author.md`, `clutch/specs/requisition_review.md` and `clutch/docs/host-authoring.md` say nothing about which documents are frozen. So the wording gap is real, but the evidence shows no harmful runtime behavior. Reopen if either of these is shown: (a) another Author or roadmap draft bars, or fails to fence, a plan document that its change makes false, and that draft merges or spends a run attempt; or (b) a stale plan Status section causes wrong engine behavior, such as Author or the roadmap driver drafting from a false Status, or a release audit failing because of it.

- The message reports one Author draft (boundary-contract-authoring) whose Scope out barred edits to docs/boundary-contract-plan.md; a supervising session corrected it by hand before any run.
- boundary-contract-authoring is in the merged set, with the corrected fence.
- A grep of clutch/specs/author.md, clutch/specs/requisition_review.md and clutch/docs/host-authoring.md finds no rule naming CLUTCH_PLAN.md as the only frozen document and no rule requiring a plan's Status section to be updated (host-authoring.md:133 covers only how plan or roadmap edits are verified).
- Earlier stale-plan-document reports were all declined as documentation wording with no runtime harm: declined-box-000526, -000530, -000594, -000621, -000627, -000646, -000656.

Message: box-000756-c97e1d39
