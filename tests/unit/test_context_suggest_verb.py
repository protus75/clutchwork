# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: context suggest verb outcomes and exit codes
# relates: [clutch/__main__.py]
# owner: engine
# verified: be8ec7c3
# hash: 3a1d5c3a2fdff5a279a0cd4f1398b971c6665c71b87a11fc05195f9adf608412
import argparse
from pathlib import Path
from types import SimpleNamespace

import duckdb
import pytest

from clutch.__main__ import _parser, _run_context_suggest, main


class FS:
    def __init__(self, body=b"## Goal / Why\n`index build`\n## Scope fence\n- file\n", present=True):
        self.body, self.present = body, present

    def read_bytes(self, path):
        if self.body is None:
            raise FileNotFoundError(path)
        return self.body

    def size(self, path):
        if not self.present:
            raise FileNotFoundError(path)
        return 1


def test_outcomes(capsys):
    config = SimpleNamespace(state_dir=Path("/state"))

    def connect(path, *, read_only):
        assert (path, read_only) == ("/state/index.duckdb", True)
        conn = duckdb.connect(":memory:")
        conn.execute("CREATE TABLE files (path VARCHAR)")
        conn.execute("CREATE TABLE chunks (path VARCHAR, selector VARCHAR, text VARCHAR)")
        conn.execute("CREATE TABLE touches (ticket VARCHAR, path VARCHAR)")
        conn.execute("INSERT INTO files VALUES ('other')")
        conn.execute("INSERT INTO touches VALUES ('past', 'file'), ('past', 'other')")
        return conn

    def run(stem, fs, c=connect):
        return _run_context_suggest(config, Path("/repo"), stem, fs=fs, connect=c)

    assert run("demo", FS()) == 0
    assert capsys.readouterr().out == "context suggest: suggested\n- other  # changed with file in 1 past tickets\n"
    assert run("demo", FS(b"## Goal / Why\ntext\n## Scope fence\n- unknown\n")) == 0
    assert capsys.readouterr().out == "context suggest: none\n"
    for stem, fs in [("Bad_Stem", FS()), ("decisions", FS()), ("demo", FS(None)), ("demo", FS(b"\xff")), ("demo", FS(b"## Goal / Why\n\n## Scope fence\n- f")), ("demo", FS(b"## Goal / Why\ntext"))]:
        assert run(stem, fs) == 2
        err = capsys.readouterr().err
        assert "refused" in err and " -- " in err and "Traceback" not in err
    assert run("demo", FS(present=False)) == 2
    assert "no_index -- run clutch index build" in capsys.readouterr().err

    def bad(*args, **kwargs):
        raise duckdb.Error("bad")

    assert run("demo", FS(), bad) == 2
    assert "index_unreadable -- " in capsys.readouterr().err


def test_parser():
    parser = _parser()
    assert parser.parse_args(["context", "suggest", "x"]).context_verb == "suggest"
    for args in (["context"], ["context", "suggest"], ["context", "suggest", "a", "b"]):
        with pytest.raises(SystemExit) as exc:
            parser.parse_args(args)
        assert exc.value.code == 2
    group = next(a for a in parser._actions if isinstance(a, argparse._SubParsersAction)).choices["context"]
    command = next(a for a in group._actions if isinstance(a, argparse._SubParsersAction)).choices["suggest"]
    assert group.description and "clutch context suggest my-ticket" in group.format_help()
    assert all(x in command.format_help() for x in ("Reads:", "Writes:", "Lock:", "Exit codes:", "Examples:", "clutch context suggest my-ticket"))
    assert "context suggest" in parser.format_help()


def test_main_no_index(tmp_path, capsys):
    (tmp_path / "config.yaml").write_text("""schema_version: 1
state_dir: .clutch/state
providers:
  - name: claude
    kind: cli
    package: test-cli
    models_by_tier: {low: m, medium: m, high: m, max: m}
    limits: {concurrency: 1}
routing:
  - {tier: medium, surface: implement, candidates: [{provider: claude}]}
review: {}
merge: {}
engine_plane_safety_inventory: [config.yaml]
""")
    path = tmp_path / "tickets/demo/ticket.md"
    path.parent.mkdir(parents=True)
    path.write_text("## Goal / Why\ntext\n## Scope fence\n- file\n")
    assert main(["context", "suggest", "demo"], cwd=tmp_path) == 2
    assert "no_index" in capsys.readouterr().err
