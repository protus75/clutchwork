# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Checks the plan-ticket-serve prompt uses serve instead of drain, shares drain's limits, and is listed in the run guide and how-clutch-works
# relates: [clutch/ask.py, clutch/config.py, tests/integration/test_config.py]
# owner: engine
# verified: 18f3cf87
# hash: 30159213f5b6a4790fb921c5230dde69e4b567a2f11b94c6efcb13808848e583
from pathlib import Path

import pytest

from clutch import ask
from clutch.config import load_config
from tests.config_helpers import VALID

pytestmark = pytest.mark.disk_io_skip


def test_serve_prompt_and_docs(tmp_path):
    (tmp_path / "config.yaml").write_text(VALID.replace("state_dir: .clutch", "state_dir: custom/state"))
    config = load_config(None, cwd=tmp_path)
    serve = ask.render("plan-ticket-serve", "", config, tmp_path)
    drain = ask.render("plan-ticket-drain", "", config, tmp_path)
    for phrase in ("Never push; publishing happens only through `clutch release publish`", "at most 3 roadmap tickets confirmed and unrun", "read the host's agent conduct files"):
        assert phrase in serve and phrase in drain
    for phrase in (
        "clutch engine serve",
        "clutch view events",
        "clutch prompt drain-loop",
        "clutch engine stop",
        "tail a drain's output or start a drain",
        "only with `clutch engine serve`",
        "idle with nothing running or confirmed unrun",
        "background-process facility",
        "picks them up live",
    ):
        assert phrase in serve
    assert "drain.out" not in serve
    assert "clutch engine drain" not in serve
    root = Path(__file__).resolve().parents[2]
    row = next(line for line in (root / "clutch/docs/host-running.md").read_text().splitlines() if line.startswith("| `prompt` |"))
    assert "plan-ticket-serve" in row
    assert any(line.startswith("| `prompt plan-ticket-serve` |") for line in (root / "docs/how-clutch-works.md").read_text().splitlines())
