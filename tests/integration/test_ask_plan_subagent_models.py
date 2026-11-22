# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Checks the plan prompts require an explicit Sonnet selection for Claude subagents and a panel from a different model family for calibration labels
# relates: [clutch/ask.py, clutch/config.py, tests/integration/test_config.py]
# owner: engine
# verified: 38957300
# hash: 58ee0ea29200e9ad7755bac26d5acac2acc2fe0f641539b3a78a5e10130e50cc
import pytest

from clutch import ask
from clutch.config import load_config
from tests.config_helpers import VALID

pytestmark = pytest.mark.disk_io_skip


@pytest.mark.parametrize("kind", ["plan-ticket-drain", "plan-ticket-serve"])
def test_plan_child_model_policy(tmp_path, kind):
    (tmp_path / "config.yaml").write_text(VALID)
    prompt = ask.render(kind, "", load_config(None, cwd=tmp_path), tmp_path)
    for requirement in (
        "For every Claude subagent, explicitly select a Sonnet model in the host agent facility",
        "an Opus parent must never implicitly promote its children",
        "row authors, adversarial auditors, phase-closing reviewers, and open-decision proposal and judge agents",
        "Non-Claude agents retain their selected provider and model",
        "If explicit child-model selection is unavailable, report that limitation rather than silently inheriting Opus",
        "Calibration and baseline labels come from an AI panel of a different model family than the judge",
    ):
        assert requirement in prompt
