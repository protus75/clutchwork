# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test ask drain loop
# relates: [clutch/__main__.py, clutch/ask.py]
# owner: engine
# verified: 0a308920
# hash: b7b8fd595201cf7949e41224aa7a4cdc38c019c040413dbf9ff471154d4b7b42
from pathlib import Path
from types import SimpleNamespace

from clutch import __main__ as entry
from clutch import ask


def setup_prompt(monkeypatch):
    config = SimpleNamespace(state_dir=Path("/repo/custom"), ask_notes=None)
    monkeypatch.setattr(entry, "load_config", lambda *a, **k: config)
    monkeypatch.setattr(entry, "child_env", lambda *a: {})
    monkeypatch.setattr(Path, "read_text", lambda self: "/loop ${state_dir}/drain.out")
    return config


def test_render_drain_loop_unit(monkeypatch):
    config = setup_prompt(monkeypatch)
    assert ask.render("drain-loop", "", config, Path("/repo")) == "/loop custom/drain.out"  # A fixed or absolute path differs.


def test_prompt_verb_drain_loop_prints_unit(monkeypatch, capsys):
    setup_prompt(monkeypatch)
    assert entry.main(["prompt", "drain-loop"], cwd=Path("/repo")) == 0  # Refusing the prompt differs.
    assert capsys.readouterr().out == "/loop custom/drain.out"  # An empty or wrong print differs.


def test_prompt_verb_drain_loop_refuses_stem(monkeypatch, capsys):
    setup_prompt(monkeypatch)
    assert entry.main(["prompt", "drain-loop", "x"]) == 2  # Ignoring the stem succeeds instead.
    assert "drain-loop takes no stem" in capsys.readouterr().err  # A generic refusal differs.


def test_prompt_verb_ticket_kind_still_requires_stem(monkeypatch, capsys):
    setup_prompt(monkeypatch)
    assert entry.main(["prompt", "review"]) == 2  # Accepting a missing stem succeeds instead.
    assert "exactly one stem" in capsys.readouterr().err  # A different refusal loses the requirement.
