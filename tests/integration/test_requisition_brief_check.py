# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Checks that the requisition_review Task section stays brief and that the plan-ticket drain and serve prompts point to `clutch ticket review`
# relates: [clutch/specs/__init__.py]
# owner: clutch/specs/__init__.py
# verified: 38957300
# hash: ad352f64e2be46f20fa82eb350eaa43a8ce44647152e14d7d8c06e076ef08991
from pathlib import Path

import pytest

from clutch import ask
from clutch.config import load_config
from tests.config_helpers import VALID

pytestmark = pytest.mark.disk_io_skip

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
