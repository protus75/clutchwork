from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_guide_rejects_standing_document_content_tests():
    text = (ROOT / "clutch/docs/host-authoring.md").read_text()
    section = text.split("## Keeping tickets apart\n", 1)[1].split("\n## ", 1)[0]
    # Removing the new bullet must not pass because unrelated sections mention these words.
    bullet = next(b for b in section.split("\n- ") if "standing test" in b)
    assert all(phrase in bullet for phrase in ("standing test", "plan document", "gate commands are valid"))


def test_requisition_review_snags_standing_document_content_tests():
    text = (ROOT / "clutch/specs/requisition_review.md").read_text()
    task = text.split("## Task\n", 1)[1].split("## Inputs\n", 1)[0]
    # A different snag mentioning the roadmap must not substitute for this rule.
    snag = next(b for b in task.split("\n- ") if "standing test" in b)
    assert all(phrase in snag for phrase in ("standing test", "roadmap", "plan document"))
