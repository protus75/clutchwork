# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Checks the supervising prompts state priority order and repair dependencies on replaced stems before authoring and confirming
# relates: [clutch/ask.py, clutch/config.py, tests/integration/test_config.py]
# owner: engine
# verified: 38957300
# hash: bb9e9704a3f3ccb4ba8b90fd5eecb9a849877d9c3588d15dead0df2e452b2cf5
import pytest

from clutch import ask
from clutch.config import load_config
from tests.config_helpers import VALID

pytestmark = pytest.mark.disk_io_skip


@pytest.mark.parametrize("kind", ["plan-ticket-drain", "plan-ticket-serve", "drain-loop"])
def test_tick_prioritizes_and_repoints(kind, tmp_path):
    (tmp_path / "config.yaml").write_text(VALID)
    text = ask.render(kind, "", load_config(None, cwd=tmp_path), tmp_path)
    tick = text.split("Each tick:", 1)[1] if kind == "drain-loop" else text.split("Supervising:", 1)[1]
    priority = tick.index("Priority is the order")
    replaced = tick.index("Replaced stems")
    queue = tick.index("Run `clutch view status`", replaced)
    assert priority < replaced < tick.index("authoring")
    assert replaced < tick.index("confirming")
    priority_rule = tick[priority:replaced]
    replaced_rule = tick[replaced:queue]
    assert priority_rule.index("P0") < priority_rule.index("P3")
    assert "clutch view snapshot" in replaced_rule
    assert "## Depends on" in replaced_rule
