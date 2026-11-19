---
id: declined-box-000773-2d21b8d4
kind: declined
link: box-000773-2d21b8d4
reopen_after_days: 30
---
Adding a member to ENGINE_LLM_SURFACES also forces new STEP_KINDS entries in clutch/observe.py. That in turn forces an edit to the step icon table in vscode-clutchwork/extension.js, which tests/integration/test_step_icons.py requires to match STEP_KINDS entry for entry. The merge-model-resolve Author draft fenced neither file, and a supervising session added them by hand before any run. The note proposes listing these specific consumers in the fence-closure registry test and in requisition_review.md.

The general rule this incident needed is already in place. Merged tickets fence-closure-registries and set-membership-fence-closure put it in requisition_review.md and host-authoring.md: when an entry of an in-code registry or closed vocabulary changes, grep tests/ for the collection's name and fence every file holding a table that a test requires to match the collection entry for entry. That covers the chain here. tests/unit/test_step_names_cover_surfaces.py ties ENGINE_LLM_SURFACES to STEP_NAMES and STEP_KINDS, and test_step_icons.py requires extension.js's icon table to equal STEP_KINDS. The miss was the draft not applying an existing rule, not a missing rule. It was also fixed before dispatch, so no Implement attempt, cap or review cycle was spent. The proposed repair also misreads the test. test_fence_closure_registries.py only checks that the rule's phrases appear in the spec and the guide; it does not trace any registry. Listing one registry's consumers there would be an enumerated special case that goes stale and does not stop the class. Reopen if, within 30 days, a ticket that changes ENGINE_LLM_SURFACES or STEP_KINDS passes requisition review without fencing extension.js or test_step_icons.py and then fails a run, which would show that the generic rule does not reach transitive registry chains.

- tests/integration/test_fence_closure_registries.py only asserts that rule phrases appear in clutch/specs/requisition_review.md and clutch/docs/host-authoring.md. It names no registry and no consumer file.
- Its PHRASES include 'every file holding a table that a test requires to match the collection entry for entry', which already covers extension.js against test_step_icons.py.
- tests/integration/test_step_icons.py:21 asserts set(icons) == set(STEP_KINDS), so a grep for STEP_KINDS finds it.
- tests/unit/test_step_names_cover_surfaces.py links ENGINE_LLM_SURFACES to STEP_NAMES and STEP_KINDS, so a grep for ENGINE_LLM_SURFACES leads to the STEP_KINDS chain.
- The message says the supervising session fixed the merge-model-resolve fence by hand before any run, so no run was harmed.
- Merged stems fence-closure-registries and set-membership-fence-closure already own this rule.

Message: box-000773-2d21b8d4
