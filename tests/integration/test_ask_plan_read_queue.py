# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Checks supervising prompts begin each tick by reading the current queue from view snapshot and view status, never from memory
# relates: [clutch/ask.py, clutch/config.py, tests/integration/test_config.py]
# owner: engine
# verified: d32c32ad
# hash: 1ce8a2de9bf2cecaab5bbf4b67b9ea72081de50099d40bcd78a0e8af9f79919c
import pytest

from clutch import ask
from clutch.config import load_config
from tests.integration.test_config import VALID

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
