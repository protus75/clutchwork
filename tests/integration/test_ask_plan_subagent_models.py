# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test rendered plan subagent model policy
# relates: [clutch/ask.py, clutch/config.py, tests/integration/test_config.py]
# owner: engine
# verified: 0c49d7b5
# hash: 69ad79e5b8a02633becdf6158363bb96571363587cc1f45095d8b430a07b379b
import pytest

from clutch import ask
from clutch.config import load_config
from tests.integration.test_config import VALID


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
