# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test ask plan serve
# relates: [clutch/ask.py, clutch/config.py, tests/integration/test_config.py]
# owner: engine
# verified: 148a8874
# hash: 0e26fae02e4f1b9ba726cc5ae3f444fe6ab9d344487c330a000084661be8cd2b
from pathlib import Path

from clutch import ask
from clutch.config import load_config
from tests.integration.test_config import VALID


def test_serve_prompt_and_docs(tmp_path):
    (tmp_path / "config.yaml").write_text(VALID.replace("state_dir: .clutch", "state_dir: custom/state"))
    config = load_config(None, cwd=tmp_path)
    serve = ask.render("plan-ticket-serve", "", config, tmp_path)
    drain = ask.render("plan-ticket-drain", "", config, tmp_path)
    for phrase in ("Never push; publishing happens only through the driver", "at most 3 roadmap tickets confirmed and unrun", "read the host's agent conduct files"):
        assert phrase in serve and phrase in drain
    for phrase in (
        "clutch engine serve",
        "clutch view events",
        "clutch prompt drain-loop",
        "clutch engine stop",
        "tail a drain's output or start a drain",
        "custom/state/engine.log",
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
