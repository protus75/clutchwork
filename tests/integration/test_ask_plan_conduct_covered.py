# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Plan prompts check conduct rules before running verbs
# relates: [clutch/ask.py, clutch/config.py, tests/integration/test_config.py]
# owner: engine
# verified: 75d75946
# hash: 8cc4d3d8f0bf363bc9a05e320376b1a01512672d7ebd97e2fe52892c3895738e
import pytest

from clutch import ask
from clutch.config import load_config
from tests.integration.test_config import VALID


@pytest.mark.parametrize("kind", ["plan-ticket-drain", "plan-ticket-serve"])
def test_conduct_check_precedes_verbs_and_distinguishes_conflicts(kind, tmp_path):
    (tmp_path / "config.yaml").write_text(VALID)
    text = ask.render(kind, "", load_config(None, cwd=tmp_path), tmp_path)

    assert text.index("run no clutch verb") < text.index("clutch view status")
    assert "running this prompt is the owner's explicit override" in text
    assert "is covered" in text.split("Before you start:", 1)[1].split("\n- ", 2)[1]
    assert "one message that ends with the question" in text
    assert "run nothing until the owner answers" in text
    assert "no uncovered rule, say so and continue without waiting" in text
    assert "forbids them is covered, not a conflict" in text
