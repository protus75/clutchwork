# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test brief requisition and plan prompts
# relates: [clutch/specs/__init__.py]
# owner: clutch/specs/__init__.py
# verified: 595b9e84
# hash: b57309ed91524eabc8b86fef854af63d3d064de87b7a41d4e9e3a38f3c75eb15
from pathlib import Path

from clutch import ask
from clutch.config import load_config
from tests.integration.test_config import VALID

ROOT = Path(__file__).resolve().parents[2]


def test_brief_task_and_plan_prompts(tmp_path):
    (tmp_path / "config.yaml").write_text(VALID)
    config = load_config(None, cwd=tmp_path)
    text = (ROOT / "clutch/specs/requisition_review.md").read_text()
    task = text.split("## Task\n", 1)[1].split("## Inputs\n", 1)[0]
    for phrase in ("Account for every listed dependent", "`dependents`", "Trace the reference closure", "grep `tests/`"):
        assert phrase not in task
    for name in ("drain", "serve"):
        prompt = ask.render(f"plan-ticket-{name}", "", config, tmp_path)
        assert "for adversarial audit" not in prompt
        assert "clutch ticket review" in prompt
        assert "Run `clutch prompt review <stem>` for a full audit only when the owner asks for one." in prompt
