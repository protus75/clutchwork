# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Checks the supervising prompts start each tick by reading the current queue from view snapshot and view status, never from memory
# relates: [clutch/ask.py, clutch/config.py, tests/integration/test_config.py]
# owner: engine
# verified: 38957300
# hash: a47666208e9cba17148670b8f28e3d1b13da2c6b5ef1a97b6c794824c8803072
import pytest

from clutch import ask
from clutch.config import load_config
from tests.config_helpers import VALID

pytestmark = pytest.mark.disk_io_skip


@pytest.mark.parametrize("kind", ["plan-ticket-drain", "plan-ticket-serve", "drain-loop"])
def test_tick_reads_current_queue(kind, tmp_path):
    (tmp_path / "config.yaml").write_text(VALID)
    text = ask.render(kind, "", load_config(None, cwd=tmp_path), tmp_path)
    tick = text.split("Each tick:", 1)[1] if kind == "drain-loop" else text.split("Supervising:", 1)[1]
    rule = tick.lstrip().splitlines()[0]
    for phrase in (
        "clutch view snapshot",
        "clutch view status",
        "never from memory",
        "did not author",
        "work in flight",
        "count it toward the window",
        "time of the command",
    ):
        assert phrase in rule, phrase
    assert tick.index("clutch view snapshot") < tick.index("confirming")
    assert tick.index("clutch view snapshot") < tick.index("authoring")
