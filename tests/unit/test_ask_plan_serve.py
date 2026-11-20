# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test ask plan serve
# relates: [clutch/__main__.py, clutch/ask.py]
# owner: engine
# verified: 0a308920
# hash: 5b907bb64cf9383e34de9da3dde1eedefc3844e494ae08a1f86dc53681c3e789
from pathlib import Path
from types import SimpleNamespace

from clutch import __main__ as entry
from clutch import ask


def test_serve_render_and_cli(monkeypatch, tmp_path, capsys):
    config = SimpleNamespace(state_dir=tmp_path / "custom", ask_notes=None)
    monkeypatch.setattr(entry, "load_config", lambda *a, **k: config)
    monkeypatch.setattr(entry, "child_env", lambda *a: {})
    monkeypatch.setattr(Path, "read_text", lambda self: self.name + " ${state_dir}")
    assert ask.render("plan-ticket-serve", "", config, tmp_path) == "plan-ticket-serve.md custom"
    assert entry.main(["prompt", "plan-ticket-serve"], cwd=tmp_path) == 0
    assert capsys.readouterr().out == "plan-ticket-serve.md custom"
    assert entry.main(["prompt", "plan-ticket-serve", "x"], cwd=tmp_path) == 2
    assert "plan-ticket-serve takes no stem" in capsys.readouterr().err
