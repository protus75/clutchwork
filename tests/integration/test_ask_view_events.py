# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Checks the plan-ticket-drain and drain-loop prompts monitor with clutch view events, and that the docs and README list the verb
# relates: [clutch/ask.py, clutch/config.py, tests/integration/test_config.py]
# owner: engine
# verified: 38957300
# hash: b09d64156e0d83918eb10a37080eb523ff63e0680154ae51b57cd01e81fb6347
from pathlib import Path

import pytest

from clutch import ask
from clutch.config import load_config
from tests.config_helpers import VALID

pytestmark = pytest.mark.disk_io_skip


def test_prompts_and_docs(tmp_path):
    (tmp_path / "config.yaml").write_text(VALID)
    config = load_config(None, cwd=tmp_path)
    for name in ("plan-ticket-drain", "drain-loop"):
        text = ask.render(name, "", config, tmp_path)
        assert "clutch view events" in text  # A prompt without the new command differs.
        assert "monitor facility" in text  # A prompt without monitoring differs.
    root = Path(__file__).resolve().parents[2]
    assert any(line.startswith("| `view events` |") for line in (root / "docs/how-clutch-works.md").read_text().splitlines())
    assert "uv run clutch view events" in (root / "README.md").read_text()
