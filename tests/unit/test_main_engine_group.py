# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test main engine group
# relates: [clutch/__main__.py]
# owner: clutch/__main__.py
# verified: 0a308920
# hash: 0f49961b936301377b519a3466e37bf8a8a32cd4cbac6d8caea19063fd361d46
import argparse

import pytest

from clutch.__main__ import _parser, main


def children(parser):
    return next(a for a in parser._actions if isinstance(a, argparse._SubParsersAction)).choices


def test_engine_group_owns_the_four():
    top = children(_parser())
    verbs = {"drain", "serve", "run", "stop"}
    assert verbs <= children(top["engine"]).keys()
    assert not verbs & top.keys()


@pytest.mark.parametrize("argv", [["drain"], ["serve"], ["run", "x"], ["stop"]])
def test_old_names_are_refused(argv, tmp_path, capsys):
    with pytest.raises(SystemExit) as error:
        main(argv, cwd=tmp_path, env={})
    assert error.value.code == 2
    assert "invalid choice" in capsys.readouterr().err


def test_subcommands_keep_their_arguments():
    parser = _parser()
    args = parser.parse_args(["engine", "drain", "--detach", "--parked", "a", "--parked", "b", "--deadline", "2026-01-01T02:00:00+00:00"])
    assert args.detach is True
    assert args.parked == ["a", "b"]
    assert args.deadline is not None
    assert parser.parse_args(["engine", "run", "x"]).stem == "x"
    assert parser.parse_args(["engine", "serve"]).engine_verb == "serve"
    assert parser.parse_args(["engine", "stop"]).engine_verb == "stop"
    with pytest.raises(SystemExit) as error:
        parser.parse_args(["engine", "run"])
    assert error.value.code == 2


@pytest.mark.parametrize("argv", [["engine", "drain"], ["engine", "serve"], ["engine", "run", "x"], ["engine", "stop"]])
def test_refusal_names_the_group(argv, tmp_path, capsys):
    assert main(argv, cwd=tmp_path, env={}) == 2
    out = capsys.readouterr()
    assert out.out == ""
    assert len(out.err.splitlines()) == 1
    assert out.err.startswith("clutch engine: ")
    assert "config file not found" in out.err
