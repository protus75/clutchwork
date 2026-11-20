# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test main engine control
# relates: [clutch/__main__.py]
# owner: clutch/__main__.py
# verified: 0a308920
# hash: ddd6e1202babb59b7f6c8f858bc40e89e6356b9389adc76346b2cb7acc2f9aee
import argparse

import pytest

from clutch.__main__ import _parser, main

CONTROL = ("pause", "resume", "kill", "retro")


def children(parser):
    return next(action for action in parser._actions if isinstance(action, argparse._SubParsersAction)).choices


def test_engine_group_owns_the_control_verbs():
    top = children(_parser())
    verbs = set(CONTROL) | {"drain", "serve", "run", "stop"}
    assert verbs <= children(top["engine"]).keys()
    assert not verbs & top.keys()


@pytest.mark.parametrize("verb", CONTROL)
def test_old_control_names_are_refused(verb, tmp_path, capsys):
    with pytest.raises(SystemExit) as error:
        main([verb], cwd=tmp_path, env={})
    assert error.value.code == 2
    assert "invalid choice" in capsys.readouterr().err


def test_control_subcommands_take_no_arguments():
    parser = _parser()
    for verb in CONTROL:
        assert parser.parse_args(["engine", verb]).engine_verb == verb
    with pytest.raises(SystemExit) as error:
        parser.parse_args(["engine", "kill", "x"])
    assert error.value.code == 2


@pytest.mark.parametrize("verb", CONTROL)
def test_control_refusal_names_the_group(verb, tmp_path, capsys):
    assert main(["engine", verb], cwd=tmp_path, env={}) == 2
    out = capsys.readouterr()
    assert out.out == ""
    assert len(out.err.splitlines()) == 1
    assert out.err.startswith("clutch engine: ")
    assert "config file not found" in out.err
    if verb == "retro":
        assert out.err.rstrip().endswith("-- repair the selected config and retry engine retro")
    else:
        assert "retry" not in out.err
