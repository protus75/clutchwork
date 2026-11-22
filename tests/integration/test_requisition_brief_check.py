# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Checks that the requisition_review Task section stays brief and that the plan-ticket drain and serve prompts point to `clutch ticket review`
# relates: [clutch/specs/__init__.py]
# owner: clutch/specs/__init__.py
# verified: d32c32ad
# hash: ebc9192cc39576d81de7db8fdd94dcf0e2344210df5477a31585b0e8443b7621
from pathlib import Path

import pytest

from clutch import ask
from clutch.config import load_config
from tests.integration.test_config import VALID

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
