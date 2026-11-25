# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Unit tests for the `clutch index query` CLI verb: output formatting, refusal exit codes, parser help text, and lock-free dispatch.
# relates: [clutch/__main__.py, clutch/index.py]
# owner: clutch/__main__.py
# verified: 8b0df903
# hash: 5a9da340ed9c9cb1e2106d33c756341321148f9f23d88c888d0b5569ae6a5f26
import argparse
import asyncio
from pathlib import Path
from types import SimpleNamespace as NS

import pytest

from clutch import index
from clutch.__main__ import _parser, _run_index_query


def invoke(result, capsys):
    async def query(config, root, text, **kwargs):
        assert text == "topic" and kwargs["limit"] == 3
        return result

    config = NS(providers=[], release=NS(pypi_token=None))
    code = asyncio.run(_run_index_query(config, Path("/repo"), "topic", fs=None, exec_=None, env={}, creator=None, limit=3, query=query))
    return code, capsys.readouterr()


def test_output(capsys):
    hit = index.QueryHit("a.py", "code", "a.py::x", "purpose", ("b", "c"), "team", 1.0)
    code, out = invoke(index.QueryResult("found", "fulltext", (hit,)), capsys)
    assert (code, out.out, out.err) == (0, "index query: found\n- a.py::x  # [code], purpose, owner: team, relates: b, c\n", "")
    code, out = invoke(index.QueryResult("no_match"), capsys)
    assert (code, out.out, out.err) == (0, "index query: none\n", "")


@pytest.mark.parametrize("outcome", ["invalid_input", "no_index", "index_unreadable", "fulltext_unavailable"])
def test_refusals(outcome, capsys):
    code, out = invoke(index.QueryResult(outcome), capsys)
    assert code == 2 and out.out == "" and out.err.startswith("clutch index query: " + outcome + " -- ")


def test_parser():
    parser = _parser()
    args = parser.parse_args(["index", "query", "topic", "--limit", "4"])
    assert (args.index_verb, args.text, args.limit) == ("query", "topic", 4)
    group = next(a for a in parser._actions if isinstance(a, argparse._SubParsersAction)).choices["index"]
    command = next(a for a in group._actions if isinstance(a, argparse._SubParsersAction)).choices["query"]
    assert "clutch index build" in group.format_help() and "clutch index query" in group.format_help()
    assert all(part in command.format_help() for part in ("Reads:", "Writes:", "Lock:", "Exit codes:", "Examples:", "clutch index query"))


def test_dispatch_does_not_lock(monkeypatch, capsys):
    from clutch import __main__ as cli

    config = NS(state_dir=Path("/state"), providers=[], release=NS(pypi_token=None))
    monkeypatch.setattr(cli, "load_config", lambda *a, **k: config)

    def locked(*args, **kwargs):
        raise AssertionError("query acquired writer lock")

    monkeypatch.setattr(cli, "_locked", locked)

    async def query(config, root, text, **kwargs):
        assert (root, text, kwargs["limit"]) == (Path("/repo"), "search", 7)
        return 0

    monkeypatch.setattr(cli, "_run_index_query", query)
    assert cli.main(["index", "query", "search", "--limit", "7"], cwd=Path("/repo"), env={}) == 0
