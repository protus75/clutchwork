# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test authoring document test rule
# relates: []
# owner: engine
# verified: 595b9e84
# hash: b6427a9036dff29f6ef3583ba872807ceb1bbb18bfb027d716d572617cfc321a
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_guide_rejects_standing_document_content_tests():
    text = (ROOT / "clutch/docs/host-authoring.md").read_text()
    section = text.split("## Keeping tickets apart\n", 1)[1].split("\n## ", 1)[0]
    # Removing the new bullet must not pass because unrelated sections mention these words.
    bullet = next(b for b in section.split("\n- ") if "standing test" in b)
    assert all(phrase in bullet for phrase in ("standing test", "plan document", "gate commands are valid"))
