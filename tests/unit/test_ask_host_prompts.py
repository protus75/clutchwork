# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Unit tests for the host prompt catalog and rendering from prompts_dir, ask_notes injection, and reporting of invalid prompt files
# relates: [clutch/ask.py, clutch/config.py, tests/config_helpers.py]
# owner: engine
# verified: f74aec75
# hash: a4293cf1d7b1638b380229c52754bd38a29268c13fc368ce1748c56769048519
import pytest

from clutch import ask
from clutch.config import load_config
from tests.config_helpers import VALID


def config(tmp_path, extra=""):
    (tmp_path / "config.yaml").write_text(VALID + extra)
    return load_config(None, cwd=tmp_path)


def test_catalog_and_render(tmp_path):
    cfg = config(tmp_path, "prompts_dir: prompts\nask_notes: Guidance\n")
    assert config(tmp_path).prompts_dir is None  # A default directory would be visible.
    assert cfg.prompts_dir == tmp_path / "prompts"  # Resolving against cwd elsewhere would differ.
    cfg.prompts_dir.mkdir()
    (cfg.prompts_dir / "zeta.md").write_text("---\ndescription: Zeta\ntakes: none\n---\n$state_dir")
    (cfg.prompts_dir / "notes.md").write_text("---\ndescription: Notes\ntakes: stem\n---\n$stem $ticket $state_dir")
    entries, problems = ask.catalog(cfg, tmp_path)
    assert not problems
    assert set(ask.DESCRIPTIONS) == set(ask.TAKES) == set(ask.KINDS)
    assert [e["argv"] for e in entries] == [["prompt", k] for k in ask.KINDS] + [["prompt", "host", "notes"], ["prompt", "host", "zeta"]]
    rendered = ask.render_host("notes", "example", cfg, tmp_path)
    assert "example tickets/example/ticket.md .clutch" in rendered
    assert "host_notes" in rendered and "Guidance" in rendered


@pytest.mark.parametrize(
    ("name", "content"),
    [
        ("missing", "takes: none"),
        ("extra", "description: X\ntakes: none\nextra: x"),
        ("boxy", "description: X\ntakes: box"),
        ("Bad_Name", "description: X\ntakes: none"),
        ("unknown", "description: X\ntakes: none\n---\n$nope"),
    ],
)
def test_invalid_files_are_reported(tmp_path, name, content):
    cfg = config(tmp_path, "prompts_dir: prompts\n")
    cfg.prompts_dir.mkdir()
    path = cfg.prompts_dir / f"{name}.md"
    path.write_text(f"---\n{content}\n---\nbody")
    entries, problems = ask.catalog(cfg, tmp_path)
    assert [p for p, _ in problems] == [path]  # Dropping invalid files silently differs.
    assert all(e["name"] != name for e in entries)
    with pytest.raises(ValueError, match=name):
        ask.render_host(name, "", cfg, tmp_path)
