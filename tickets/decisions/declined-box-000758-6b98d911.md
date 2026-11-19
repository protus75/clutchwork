---
id: declined-box-000758-6b98d911
kind: declined
link: box-000758-6b98d911
reopen_after_days: 30
---
Line 453 of tests/integration/test_rework.py checks the SHA-256 of rework.md's rendered fixture against a fixed digest. Any wording change to clutch/specs/rework.md therefore also forces an edit to this test. That happened on specs-explain-quoted-delimiter: the test was outside the fence, so Implement attempt 0 bounced premise_failed, the ticket went to the Reject queue, and it was rewritten to fence the test. The proposal replaces the digest with structural checks on the named data blocks and their order.

The described cost is real: line 453 pins a hardcoded sha256 of the render, and line 454 already checks that validate_data_blocks is empty and that no placeholders are left. Still, this is a test-only change and is not tied to reachable incorrect runtime behavior. The engine renders and runs Rework correctly with or without the digest. The harm was authoring friction on one ticket whose fence missed a test that pins a changed value. The existing fence-closure rule already covers that case: fence the tests that pin a changed name, value or version. It was fixed by a ticket rewrite, and specs-explain-quoted-delimiter has since merged. Decision box-000593 declined the same pattern, a test pinning exact content that forced a test edit on every content change, for the same reason. Reopen if a second ticket that edits clutch/specs/rework.md bounces premise_failed or goes to the Reject queue because test_rework.py:453 was outside its fence. Measure it as at least one more premise_failed or Reject-queue arrival citing that digest within the window.

- tests/integration/test_rework.py:453 asserts hashlib.sha256(render(spec, fixture)).hexdigest() equals a hardcoded digest
- tests/integration/test_rework.py:454 already asserts validate_data_blocks(golden) == [] and that no fixture placeholder remains; lines 455-459 and 499-500 check each named block's quoting and open/close delimiters
- specs-explain-quoted-delimiter is in the merged set; the single incident was fixed by fencing the test
- declined-box-000593-4f13f57a declined a matching request to swap exact-content pins in a test for validity checks
- Ticket-authoring fence rule: fence tests that pin a changed name, value, or version

Message: box-000758-6b98d911
