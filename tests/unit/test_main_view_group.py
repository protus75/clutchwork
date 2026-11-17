import argparse
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from clutch import __main__ as entry
from clutch import observe


def test_view_group_parses():
    parser = entry._parser()
    a = parser.parse_args(["view", "watch"])
    assert (a.verb, a.view_verb, a.once) == ("view", "watch", False)
    assert parser.parse_args(["view", "watch", "--once"]).once is True
    for name in ("snapshot", "status"):
        assert parser.parse_args(["view", name]).view_verb == name
    a = parser.parse_args(["view", "stats"])
    assert (a.window, a.json, a.tree) == ("7d", False, False)
    a = parser.parse_args(["view", "stats", "--window", "3t", "--json", "--tree"])
    assert (a.window, a.json, a.tree) == ("3t", True, True)
    for argv in (["view"], ["view", "snapshot", "--once"], ["view", "status", "extra"], ["view", "stats", "--once"]):
        with pytest.raises(SystemExit) as exc:
            parser.parse_args(argv)
        assert exc.value.code == 2


def test_old_names_refuse():
    parser = entry._parser()
    top = next(a for a in parser._actions if isinstance(a, argparse._SubParsersAction))
    group = next(a for a in top.choices["view"]._actions if isinstance(a, argparse._SubParsersAction))
    for name in ("watch", "snapshot", "status", "stats"):
        assert name not in top.choices and name in group.choices
        with pytest.raises(SystemExit) as exc:
            parser.parse_args([name])
        assert exc.value.code == 2


def test_refusals_name_group(tmp_path, capsys):
    for argv in (["view", "watch", "--once"], ["view", "snapshot"], ["view", "status"], ["view", "stats"]):
        assert entry.main(argv, cwd=tmp_path, env={}) == 2
        out, err = capsys.readouterr()
        assert out == ""
        assert len(err.splitlines()) == 1 and err.startswith("clutch view: ") and "config file not found" in err
    assert list(tmp_path.iterdir()) == []


def test_dispatch_and_optional_locks(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(entry, "load_config", lambda *a, **kw: SimpleNamespace(state_dir=tmp_path, providers=[]))

    class Journal:
        def __init__(self, *args):
            pass

        def read(self):
            return []

    monkeypatch.setattr(entry, "Journal", Journal)
    for name in ("CommitLock", "SubprocessExec"):
        monkeypatch.setattr(entry, name, lambda *a, **kw: object())
    envs = []
    monkeypatch.setattr(entry, "Git", lambda *a, **kw: envs.append(kw["env"]) or object())
    monkeypatch.setattr(observe, "snapshot", lambda ctx: {"snapshot": 42})
    monkeypatch.setattr(observe, "text_snapshot", lambda ctx: "text view")
    monkeypatch.setattr(entry, "_status", AsyncMock(return_value="projection"))
    monkeypatch.setattr(entry, "render", lambda value: f"rendered {value}\n")
    monkeypatch.setattr(entry, "_stats", AsyncMock(return_value={"health": 7}))
    for argv, expected in (
        (["view", "snapshot"], json.dumps({"snapshot": 42}) + "\n"),
        (["view", "watch", "--once"], "text view\n"),
        (["view", "status"], "rendered projection\n"),
        (["view", "stats", "--json"], json.dumps({"health": 7}) + "\n"),
    ):
        assert entry.main(argv, cwd=tmp_path, env={}) == 0
        out, err = capsys.readouterr()
        assert (out, err) == (expected, "")
    assert [env.get("GIT_OPTIONAL_LOCKS") for env in envs] == ["0", "0", None, None]
    assert entry.main(["view", "stats", "--window", "0d"], cwd=tmp_path, env={}) == 2
    assert capsys.readouterr().err == "clutch view: bad window 0d -- use <N>h, <N>d, or <N>t\n"
