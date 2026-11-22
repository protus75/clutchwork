# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Checks plan prompts require explicit Sonnet selection for Claude subagents and different-family panels for calibration labels
# relates: [clutch/ask.py, clutch/config.py, tests/integration/test_config.py]
# owner: engine
# verified: d32c32ad
# hash: f9d886fd0d2bbd8e4d284de9c8ae89ea21edb6abe5ddfc5538825413e67c3712
import pytest

from clutch import ask
from clutch.config import load_config
from tests.integration.test_config import VALID

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
