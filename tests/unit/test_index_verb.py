# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: index build verb outcomes and exit codes
# relates: [clutch/__main__.py]
# owner: engine
# verified: 99c2ebc3
# hash: 5e6d7bac81c02c58f09040f1a095b6c95257dd1d6e5d63ef406e1dd8dc99eebe
import argparse
import asyncio
from pathlib import Path
from types import SimpleNamespace as NS

import duckdb
import pytest

from clutch.__main__ import _parser, _run_index


def invoke(findings, capsys):
    async def build(*args, **kwargs):
        if isinstance(findings, BaseException):
            raise findings
        return findings

    config = NS(providers=[NS(auth="SECRET")], release=NS(pypi_token="TOKEN"))
    code = asyncio.run(_run_index(config, Path("/repo"), fs=None, git=None, exec_=None, env={}, store=None, creator=None, build=build))
    return code, capsys.readouterr()


def test_success_and_findings(capsys):
    code, output = invoke([], capsys)
    assert (code, output.out, output.err) == (0, "index build: built\n", "")
    code, output = invoke(["git_failed: x", "call_unreadable: k"], capsys)
    assert (code, output.out, output.err) == (1, "index build: built_with_findings\ngit_failed: x\ncall_unreadable: k\n", "")


@pytest.mark.parametrize(
    ("prefix", "expected"),
    [("db_open_failed", 2), ("git_failed", 1), ("embed_failed", 1), ("call_unreadable", 1), ("box_unreadable", 1), ("vss unavailable", 1), ("fts unavailable", 1), ("mystery", 2)],
)
def test_prefixes(prefix, expected, capsys):
    code, output = invoke([prefix + ": x"], capsys)
    assert code == expected
    assert (prefix in output.err) == (expected == 2)


@pytest.mark.parametrize("findings", [["git_failed: x", "db_open_failed: bad"], ["git_failed"]])
def test_refusal(findings, capsys):
    code, output = invoke(findings, capsys)
    assert code == 2
    assert findings[-1] in output.err
    assert " -- " in output.err


@pytest.mark.parametrize("error", [OSError("disk"), RuntimeError("bad"), duckdb.Error("db")])
def test_errors(error, capsys):
    code, output = invoke(error, capsys)
    assert code == 2
    assert output.err.startswith(f"clutch index build: build raised {type(error).__name__}: {error}")
    assert "Traceback" not in output.err


def test_cancel(capsys):
    with pytest.raises(asyncio.CancelledError):
        invoke(asyncio.CancelledError(), capsys)


def test_build_arguments(capsys):
    seen = {}

    async def build(config, root, **kwargs):
        seen.update(kwargs)
        return []

    config = NS(providers=[NS(auth="SECRET")], release=NS(pypi_token="TOKEN"))
    creator, fs, git, exec_, store = (object() for _ in range(5))
    assert asyncio.run(_run_index(config, Path("/repo"), fs=fs, git=git, exec_=exec_, env={"SECRET": "key", "KEEP": "yes"}, store=store, creator=creator, build=build)) == 0
    assert seen == {"fs": fs, "git": git, "exec_": exec_, "env": {"KEEP": "yes"}, "store": store, "creator": creator}
    assert capsys.readouterr().out == "index build: built\n"


def test_parser():
    parser = _parser()
    assert parser.parse_args(["index", "build"]).index_verb == "build"
    for args in (["index"], ["index", "build", "extra"]):
        with pytest.raises(SystemExit) as exc:
            parser.parse_args(args)
        assert exc.value.code == 2
    sub = next(a for a in parser._actions if isinstance(a, argparse._SubParsersAction))
    group = sub.choices["index"]
    command = next(a for a in group._actions if isinstance(a, argparse._SubParsersAction)).choices["build"]
    assert group.description and "clutch index build" in group.format_help()
    assert command.description and all(x in command.format_help() for x in ("Reads:", "Writes:", "Lock:", "Exit codes:", "Examples:", "clutch index build"))
    assert "index build" in parser.format_help()
