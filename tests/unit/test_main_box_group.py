# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test main box group
# relates: [clutch/__main__.py, clutch/lockfile.py]
# owner: engine
# verified: 0a308920
# hash: 3a41fd36093a7cc258547925116a342210b198b95f9df497fca87d1633e6661e
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


@pytest.mark.parametrize("verb,expected", [("drain", 0), ("release", 2)])
def test_triage_lock_holder(tmp_path, monkeypatch, capsys, verb, expected):
    from contextlib import asynccontextmanager
    from types import SimpleNamespace

    from clutch.lockfile import LockHeld

    # Supply the config and git seam; no process or provider is started.
    config = SimpleNamespace(state_dir=tmp_path)
    monkeypatch.setattr(entry, "load_config", lambda *args, **kwargs: config)

    async def describe(*args):
        return "unit"

    monkeypatch.setattr(entry.Git, "describe", describe)

    @asynccontextmanager
    async def locked(*args, **kwargs):
        raise LockHeld(tmp_path, {"verb": verb})
        yield

    published = []
    monkeypatch.setattr(entry, "_locked", locked)
    monkeypatch.setattr(entry.control, "read_active", lambda *args: ("life", None))
    monkeypatch.setattr(entry.control, "publish_request", lambda *args: published.append(args[1]))
    assert entry.main(["box", "triage", "box-000001"], cwd=tmp_path, env={}) == expected
    out, err = capsys.readouterr()
    if verb == "drain":
        assert "triage submitted:" in out and len(published) == 1 and published[0].ids == ["box-000001"]
    else:
        assert "writer lock held by release" in err and not published
