# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: verify supervising prompts read the current queue
# relates: [clutch/ask.py, clutch/config.py, tests/integration/test_config.py]
# owner: engine
# verified: d3624866
# hash: 2f3d2a48c8b13d27d3842fdb6ffc6dd35146209e89a9714804212d2325625fd4
import pytest

from clutch import ask
from clutch.config import load_config
from tests.integration.test_config import VALID


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
