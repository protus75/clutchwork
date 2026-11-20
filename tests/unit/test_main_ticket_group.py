# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test main ticket group
# relates: [clutch/__main__.py]
# owner: clutch/__main__.py
# verified: 0a308920
# hash: a660d46332506d05753db9570673e4b9939eed603dd344871f1d6d34d8268a08
import argparse
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from clutch import __main__ as entry


def test_ticket_group_parses():
    parser = entry._parser()
    a = parser.parse_args(["ticket", "new", "some-stem"])
    assert (a.ticket_verb, a.stem, a.kind, a.evidence) == ("new", "some-stem", "feature", None)
    a = parser.parse_args(["ticket", "new", "some-stem", "--kind", "bug", "--evidence", "a.txt", "b.txt"])
    assert (a.kind, a.evidence) == ("bug", ["a.txt", "b.txt"])
    with pytest.raises(SystemExit) as exc:
        parser.parse_args(["ticket", "new", "some-stem", "--kind", "bug", "--evidence"])
    assert exc.value.code == 2
    assert parser.parse_args(["ticket", "lint"]).stems == []
    assert parser.parse_args(["ticket", "review", "a", "b"]).stems == ["a", "b"]
    with pytest.raises(SystemExit) as exc:
        parser.parse_args(["ticket", "review"])
    assert exc.value.code == 2
    a = parser.parse_args(["ticket", "order", "some-stem", "--runs-before"])
    assert (a.runs_before, a.priority) == ([], None)


def test_old_names_refuse():
    parser = entry._parser()
    top = next(a for a in parser._actions if isinstance(a, argparse._SubParsersAction))
    group = next(a for a in top.choices["ticket"]._actions if isinstance(a, argparse._SubParsersAction))
    for name in ("new", "lint", "review", "order"):
        assert name not in top.choices and name in group.choices
        with pytest.raises(SystemExit) as exc:
            parser.parse_args([name, "some-stem"])
        assert exc.value.code == 2


def test_ticket_new_needs_no_config(tmp_path):
    assert entry.main(["ticket", "new", "some-stem"], cwd=tmp_path) == 0
    assert (tmp_path / "tickets/some-stem/ticket.md").exists()
    assert not (tmp_path / ".clutch").exists()


def setup(monkeypatch):
    monkeypatch.setattr(entry, "load_config", lambda *a, **kw: SimpleNamespace(state_dir="state", providers=[]))
    for name in ("Journal", "CommitLock", "SubprocessExec"):
        monkeypatch.setattr(entry, name, lambda *a, **kw: object())


def test_lint_git_skips_optional_locks(monkeypatch, tmp_path):
    setup(monkeypatch)
    envs = []
    monkeypatch.setattr(entry, "Git", lambda *a, **kw: envs.append(kw["env"]) or object())
    monkeypatch.setattr(entry, "_lint", AsyncMock(return_value=0))
    monkeypatch.setattr(entry, "_order", lambda *a: 0)
    assert entry.main(["ticket", "lint"], cwd=tmp_path, env={}) == 0
    assert entry.main(["ticket", "order", "some-stem", "--priority", "P1"], cwd=tmp_path, env={}) == 0
    assert envs[0]["GIT_OPTIONAL_LOCKS"] == "0"
    assert "GIT_OPTIONAL_LOCKS" not in envs[1]


def test_refusal_names_group(monkeypatch, tmp_path, capsys):
    setup(monkeypatch)
    monkeypatch.setattr(entry, "Git", lambda *a, **kw: object())
    assert entry.main(["ticket", "order", "some-stem"], cwd=tmp_path, env={}) == 2
    assert capsys.readouterr().err == "clutch ticket: no ordering option supplied -- supply --priority or --runs-before\n"
