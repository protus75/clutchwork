import argparse
from pathlib import Path

import pytest

from clutch import __main__ as entry


def test_box_group_parses():
    parser = entry._parser()
    a = parser.parse_args(["box", "suggest", "an idea"])
    assert (a.box_verb, a.summary) == ("suggest", "an idea")
    assert parser.parse_args(["box", "triage"]).ids == []
    assert parser.parse_args(["box", "triage", "a", "b"]).ids == ["a", "b"]
    assert parser.parse_args(["box", "dismiss", "a"]).ids == ["a"]
    a = parser.parse_args(["box", "issue", "--class", "state-loss", "t", "--body", "b.md"])
    assert (a.issue_class, a.title, a.body) == ("state-loss", "t", Path("b.md"))
    assert parser.parse_args(["box", "issue", "t", "--body", "b.md"]).issue_class is None
    for args in (["box", "dismiss"], ["box", "suggest"], ["box", "issue", "--class", "state-loss", "t"]):
        with pytest.raises(SystemExit) as exc:
            parser.parse_args(args)
        assert exc.value.code == 2


def test_old_names_refuse():
    parser = entry._parser()
    top = next(a for a in parser._actions if isinstance(a, argparse._SubParsersAction))
    group = next(a for a in top.choices["box"]._actions if isinstance(a, argparse._SubParsersAction))
    for name in ("suggest", "triage", "dismiss", "issue"):
        assert name not in top.choices and name in group.choices
        with pytest.raises(SystemExit) as exc:
            parser.parse_args([name, "x"])
        assert exc.value.code == 2


def test_issue_needs_no_config(tmp_path, monkeypatch, capsys):
    (tmp_path / "body.md").write_text("evidence")
    monkeypatch.setattr(entry.issue, "link", lambda cls, title, body, scrub: f"{cls}:{title}:{body}")
    assert entry.main(["box", "issue", "--class", "state-loss", "t", "--body", "body.md"], cwd=tmp_path, env={}) == 0
    out, err = capsys.readouterr()
    assert out == "state-loss:t:evidence\n"
    assert "no secrets were scrubbed" in err
    assert not (tmp_path / ".clutch").exists()


def test_refusals_name_group(tmp_path, capsys):
    for args in (["box", "suggest", "an idea"], ["box", "triage"], ["box", "dismiss", "x"]):
        assert entry.main(args, cwd=tmp_path, env={}) == 2
        out, err = capsys.readouterr()
        assert out == ""
        assert len(err.splitlines()) == 1 and err.startswith("clutch box: ") and "config file not found" in err
