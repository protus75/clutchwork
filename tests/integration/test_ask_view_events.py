from pathlib import Path

from clutch import ask
from clutch.config import load_config
from tests.integration.test_config import VALID


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
