---
id: declined-box-000593-4f13f57a
kind: declined
link: box-000593-4f13f57a
reopen_after_days: 30
---
The roadmap gate test in tests/integration/test_roadmap_gate.py checks the exact argv of every release gate block in docs/roadmap.md. Because of that, any edit to a gate block also needs a test edit, which is what stopped the supervising session from tightening the 0.3.0 gate on 2026-11-16. The suggestion keeps the checks that parse the real file but swaps the exact-argv pins for validity checks: each release with rows has exactly one gate block, each clutch command parses with the CLI parser, the suite runs once, and the accept command runs last.

This is a test-only improvement. Pinning the exact argv makes gate edits cost an extra test change, but the engine does not run or merge anything wrongly because of it. The real runtime hazard is a malformed roadmap row or block that wedges the drain, and box-000540 already covers it as a separate record. The friction is real, but it is a maintenance cost and not a runtime defect, so it does not meet the admission bar. The owner can still fix it directly: edit the test in the same change that tightens the gate, or file a chore ticket by hand. Reopen if a gate block that the exact-argv pins accept still fails in the driver at runtime, or if the pins stop a gate fix that a merged row needs and no hand-authored ticket can get it through.

- message class suggestion, origin session: says the test pins data, not behavior
- no runtime failure is cited; the impact named is that the supervising session could not tighten the 0.3.0 gate without a code change
- the runtime risk the test guards (malformed roadmap row or block wedging drain) is a separate record, declined-box-000540-944b57a8
- task rules: test-only improvements are declined unless tied to reachable incorrect runtime behavior

Message: box-000593-4f13f57a
