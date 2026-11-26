# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test main host group
# relates: [clutch/__init__.py, clutch/__main__.py, clutch/hostfiles.py]
# owner: engine
# verified: 69d790e1
# hash: 051d8d6b60dd067ae125c1a61ee4667d77f4c1c3579075886bc095dba88c0405
import argparse
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

import clutch
from clutch import __main__ as entry
from clutch import hostfiles


def test_host_group_parses():
    parser = entry._parser()
    for name in ("core", "docs", "doctor"):
        args = parser.parse_args(["host", name])
        assert (args.verb, args.host_verb) == ("host", name)
    for argv in (["host"], ["host", "core", "--write"], ["host", "docs", "extra"], ["host", "doctor", "--once"]):
        with pytest.raises(SystemExit) as exc:
            parser.parse_args(argv)
        assert exc.value.code == 2


def test_old_names_refuse():
    parser = entry._parser()
    top = next(a for a in parser._actions if isinstance(a, argparse._SubParsersAction))
    group = next(a for a in top.choices["host"]._actions if isinstance(a, argparse._SubParsersAction))
    for name in ("core", "docs", "doctor"):
        assert name not in top.choices and name in group.choices
        with pytest.raises(SystemExit) as exc:
            parser.parse_args([name])
        assert exc.value.code == 2


def test_docs_and_doctor_need_no_config(tmp_path, capsys):
    assert entry.main(["host", "docs"], cwd=tmp_path, env={}) == 0
    out, err = capsys.readouterr()
    assert err == ""
    assert [line.split("  ")[0] for line in out.splitlines()] == [
        str(Path(clutch.__file__).parent / "docs" / f"host-{name}.md") for name in ("authoring", "running", "contract", "qwen", "antigravity", "training")
    ]
    assert entry.main(["host", "doctor"], cwd=tmp_path, env={}) == 2
    out, err = capsys.readouterr()
    assert err == ""
    lines = out.splitlines()
    assert lines[0] == "doctor: failed"
    assert [line.split()[1].rstrip(":") for line in lines[1:]] == ["venv", "config", "git", "lock", "journal", "core"]
    assert lines[2].endswith("; repair the selected config and rerun host doctor")
    assert lines[3] == "FAIL git: not checked: config did not load; fix the config and rerun host doctor"
    assert list(tmp_path.iterdir()) == []


def test_core_dispatch_and_refusals(tmp_path, monkeypatch, capsys):
    assert entry.main(["host", "core"], cwd=tmp_path, env={}) == 2
    out, err = capsys.readouterr()
    assert out == "" and len(err.splitlines()) == 1 and err.startswith("clutch host: ") and "config file not found" in err
    assert list(tmp_path.iterdir()) == []
    monkeypatch.setattr(entry, "load_config", lambda *a, **kw: object())
    path = tmp_path / "CLAUDE.md"
    monkeypatch.setattr(entry, "routed_conduct_paths", lambda *a: [path])

    def forbidden(*args, **kwargs):
        pytest.fail("checkout constructed")

    for name in ("SubprocessExec", "Git", "Journal", "CommitLock"):
        monkeypatch.setattr(entry, name, forbidden)
    assert entry.main(["host", "core"], cwd=tmp_path, env={}) == 0
    assert capsys.readouterr().out == ""
    assert path.read_bytes() == hostfiles.render(b"")
    path.write_bytes(b"project\n<!-- clutch:core beg")
    assert entry.main(["host", "core"], cwd=tmp_path, env={}) == 2
    out, err = capsys.readouterr()
    assert out == "" and err == f"clutch host: {hostfiles.MarkerCorruption()}\n"
    assert str(hostfiles.MarkerCorruption()).endswith(", then retry host core")


def test_core_roads_name_group(tmp_path, monkeypatch, capsys):
    assert hostfiles.classify_core(None).paved_road == "run `clutch host core` to insert the managed block"
    assert hostfiles.classify_core(hostfiles.render(b"", template=b"old\n")).paved_road == "run `clutch host core` to refresh the managed block"
    monkeypatch.setattr(entry, "load_config", lambda *a, **kw: SimpleNamespace(state_dir=tmp_path, providers=[]))
    for name in ("SubprocessExec", "Git", "Journal", "CommitLock"):
        monkeypatch.setattr(entry, name, lambda *a, **kw: object())
    monkeypatch.setattr(hostfiles, "stale_core", AsyncMock(return_value=["CLAUDE.md: clutch core is drifted; stale"]))
    assert entry.main(["engine", "drain"], cwd=tmp_path, env={}) == 2
    out, err = capsys.readouterr()
    assert out == ""
    assert err == "clutch engine: CLAUDE.md: clutch core is drifted; stale -- run clutch host core, then commit the conduct files and retry engine drain\n"
