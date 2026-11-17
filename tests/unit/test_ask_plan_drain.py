from pathlib import Path
from types import SimpleNamespace

from clutch import __main__ as entry
from clutch import ask


def setup(monkeypatch, tmp_path, template):
    config = SimpleNamespace(state_dir=tmp_path / "custom", ask_notes=None)
    monkeypatch.setattr(entry, "load_config", lambda *a, **k: config)
    monkeypatch.setattr(entry, "child_env", lambda *a: {})
    monkeypatch.setattr(Path, "read_text", lambda self: self.name + template)
    return config


def test_render_plan_ticket_drain_unit(monkeypatch, tmp_path):
    config = setup(monkeypatch, tmp_path, " ${state_dir}")
    assert ask.render("plan-ticket-drain", "", config, tmp_path) == "plan-ticket-drain.md custom"


def test_prompt_verb_plan_ticket_drain_unit(monkeypatch, tmp_path, capsys):
    setup(monkeypatch, tmp_path, " ${state_dir}")
    assert entry.main(["prompt", "plan-ticket-drain"], cwd=tmp_path) == 0
    assert capsys.readouterr().out == "plan-ticket-drain.md custom"
    assert entry.main(["prompt", "plan-ticket-drain", "x"], cwd=tmp_path) == 2
    assert "plan-ticket-drain takes no stem" in capsys.readouterr().err


def test_prompt_verb_author_without_ticket_unit(monkeypatch, tmp_path, capsys):
    setup(monkeypatch, tmp_path, " ${stem} ${ticket}")
    assert entry.main(["prompt", "author", "new-stem"], cwd=tmp_path) == 0
    assert capsys.readouterr().out == "author.md new-stem tickets/new-stem/ticket.md"
    assert entry.main(["prompt", "author", "Bad_Stem"], cwd=tmp_path) == 2
    assert "kebab-case" in capsys.readouterr().err
    assert entry.main(["prompt", "review", "new-stem"], cwd=tmp_path) == 2
    assert "tickets/new-stem/ticket.md does not exist" in capsys.readouterr().err
