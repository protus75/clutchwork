# Review: snag

The CLI and dispatch reuse logic is correct, but tests for criteria 1–4 are missing and docs/how-clutch-works.md still describes the removed blob-only approval skip.

## Findings

- [acceptance] docs/how-clutch-works.md:- Section 3 still says "`runner.drive` reviews committed ticket content before Implement unless the journal already records an approval for that blob." The diff removed the ticket-SHA-only bypass. Dispatch now reuses only the latest verdict for the stem, and only when it is an approval whose recorded input identity matches the current inputs. (do instead: Update this sentence in the requisition part of section 3 to describe the input-identity reuse rule and what invalidates it.)
- [acceptance] tests/integration/test_requisition_reuse.py:17 Criterion 1 requires proof that a confirmation-only (draft-to-confirmed) transition reuses the approval with zero extra preflight or model calls. No test in the four named files covers that transition. They only cover a second identical CLI review and a dispatch reuse with the identity gatherer mocked out. (do instead: Add an integration test that approves a draft ticket through `ticket review`, runs `ticket confirm`, then reviews or dispatches again. Assert no new requisition_review request and no new verdict event.)
- [acceptance] tests/integration/test_requisition_reuse.py:28 Criterion 2 requires proof that changes to Context bytes, sibling material, coverage, specs or substantive ticket text force a new review. Only a tracked code edit (clutch/thing.py) is tested. The other invalidation inputs are untested, and an approval followed by a newer rma is tested only in the unit selection test, not in the named integration files. (do instead: Add integration cases that change each named input after an approval: a Context-referenced file, an overlapping sibling ticket, coverage-map.json, a spec file, and the ticket body beyond its state line. Assert exactly one new requisition_review call each. Add a newer-rma case alongside the newer-snag case.)
- [acceptance] tests/unit/test_review_reuse_dispatch.py:31 Criterion 3 requires proof that both entry points preserve provisional (unmerged-dependency) behavior and admission-refusal precedence when reuse is in play. No test covers either: no CLI review of a ticket with an unmerged dependency and a matching recorded approval, and no refused admission alongside a reusable approval. (do instead: Add unit or integration tests in the named files. Show that a CLI review with an unmerged dependency still runs a provisional review and journals nothing despite a matching approval, and that a refused admission still refuses with no reuse and no model call at both entry points.)
- [acceptance] tests/integration/test_requisition_reuse.py:41 Criterion 4 requires proof that a CLI default-tier approval is reused by dispatch when tiers match, and that a reviewer-tier change forces exactly one new review. No test runs `ticket review` and then dispatches the same ticket at a matching tier. test_ladder.py only inserts extra scripted verdicts; it never asserts the requisition_review call count across a tier change. (do instead: Add an integration test that approves through `ticket review` and then drains at the default tier, asserting zero requisition_review requests at dispatch. Add a test that changes the effective tier (for example via an escalation rung) and asserts exactly one new requisition_review request.)

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "82425cac36a43663fe3a938a1176690570a60f90",
  "stem": "requisition-review-approval-reuse",
  "reviewed_sha": "82425cac36a43663fe3a938a1176690570a60f90",
  "summary": "The CLI and dispatch reuse logic is correct, but tests for criteria 1–4 are missing and docs/how-clutch-works.md still describes the removed blob-only approval skip.",
  "findings": [
    {
      "code": "acceptance",
      "path": "docs/how-clutch-works.md",
      "line": null,
      "message": "Section 3 still says \"`runner.drive` reviews committed ticket content before Implement unless the journal already records an approval for that blob.\" The diff removed the ticket-SHA-only bypass. Dispatch now reuses only the latest verdict for the stem, and only when it is an approval whose recorded input identity matches the current inputs.",
      "paved_road": "Update this sentence in the requisition part of section 3 to describe the input-identity reuse rule and what invalidates it.",
      "kind": null,
      "unit": null
    },
    {
      "code": "acceptance",
      "path": "tests/integration/test_requisition_reuse.py",
      "line": 17,
      "message": "Criterion 1 requires proof that a confirmation-only (draft-to-confirmed) transition reuses the approval with zero extra preflight or model calls. No test in the four named files covers that transition. They only cover a second identical CLI review and a dispatch reuse with the identity gatherer mocked out.",
      "paved_road": "Add an integration test that approves a draft ticket through `ticket review`, runs `ticket confirm`, then reviews or dispatches again. Assert no new requisition_review request and no new verdict event.",
      "kind": null,
      "unit": null
    },
    {
      "code": "acceptance",
      "path": "tests/integration/test_requisition_reuse.py",
      "line": 28,
      "message": "Criterion 2 requires proof that changes to Context bytes, sibling material, coverage, specs or substantive ticket text force a new review. Only a tracked code edit (clutch/thing.py) is tested. The other invalidation inputs are untested, and an approval followed by a newer rma is tested only in the unit selection test, not in the named integration files.",
      "paved_road": "Add integration cases that change each named input after an approval: a Context-referenced file, an overlapping sibling ticket, coverage-map.json, a spec file, and the ticket body beyond its state line. Assert exactly one new requisition_review call each. Add a newer-rma case alongside the newer-snag case.",
      "kind": null,
      "unit": null
    },
    {
      "code": "acceptance",
      "path": "tests/unit/test_review_reuse_dispatch.py",
      "line": 31,
      "message": "Criterion 3 requires proof that both entry points preserve provisional (unmerged-dependency) behavior and admission-refusal precedence when reuse is in play. No test covers either: no CLI review of a ticket with an unmerged dependency and a matching recorded approval, and no refused admission alongside a reusable approval.",
      "paved_road": "Add unit or integration tests in the named files. Show that a CLI review with an unmerged dependency still runs a provisional review and journals nothing despite a matching approval, and that a refused admission still refuses with no reuse and no model call at both entry points.",
      "kind": null,
      "unit": null
    },
    {
      "code": "acceptance",
      "path": "tests/integration/test_requisition_reuse.py",
      "line": 41,
      "message": "Criterion 4 requires proof that a CLI default-tier approval is reused by dispatch when tiers match, and that a reviewer-tier change forces exactly one new review. No test runs `ticket review` and then dispatches the same ticket at a matching tier. test_ladder.py only inserts extra scripted verdicts; it never asserts the requisition_review call count across a tier change.",
      "paved_road": "Add an integration test that approves through `ticket review` and then drains at the default tier, asserting zero requisition_review requests at dispatch. Add a test that changes the effective tier (for example via an escalation rung) and asserts exactly one new requisition_review request.",
      "kind": null,
      "unit": null
    }
  ],
  "spec_version": "1.9",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "snag"
}
```
