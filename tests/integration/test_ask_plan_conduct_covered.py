# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Checks the plan-ticket-drain and plan-ticket-serve prompts check host conduct rules before running any clutch verb and tell covered rules apart from conflicts
# relates: [clutch/ask.py, clutch/config.py, tests/integration/test_config.py]
# owner: engine
# verified: 38957300
# hash: c705b4c1e0476e2698d62a68a7efc83ecefa9112a9a2cebe275b1f91a782486b
import pytest

from clutch import ask
from clutch.config import load_config
from tests.config_helpers import VALID

pytestmark = pytest.mark.disk_io_skip


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
