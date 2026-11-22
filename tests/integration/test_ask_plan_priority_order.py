# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Checks supervising prompts state priority order and replaced-stem dependency repair before authoring and confirming
# relates: [clutch/ask.py, clutch/config.py, tests/integration/test_config.py]
# owner: engine
# verified: d32c32ad
# hash: e5601adc10ad19ec3d5d5d22bfe6292073e4d382fecf41e1ce992648b01ce0ad
import pytest

from clutch import ask
from clutch.config import load_config
from tests.integration.test_config import VALID

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
