import argparse
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from clutch import __main__ as entry


def test_verdicts_join_ticket_group():
    parser = entry._parser()
    top = next(a for a in parser._actions if isinstance(a, argparse._SubParsersAction))
    group = next(a for a in top.choices["ticket"]._actions if isinstance(a, argparse._SubParsersAction))
    for name in ("confirm", "reject"):
        assert name not in top.choices and name in group.choices
        with pytest.raises(SystemExit) as exc:
            parser.parse_args([name, "x"])
        assert exc.value.code == 2


def test_verdict_arguments_unchanged():
    parser = entry._parser()
    args = parser.parse_args(["ticket", "confirm", "a", "b"])
    assert (args.ticket_verb, args.stems, args.yes, args.extension) == ("confirm", ["a", "b"], False, False)
    args = parser.parse_args(["ticket", "reject", "--yes", "x"])
    assert (args.ticket_verb, args.yes, args.stems) == ("reject", True, ["x"])
    assert parser.parse_args(["ticket", "confirm", "--extension", "x"]).extension is True
    with pytest.raises(SystemExit) as exc:
        parser.parse_args(["ticket", "reject"])
    assert exc.value.code == 2


def test_dispatch_passes_subcommand(monkeypatch, tmp_path):
    monkeypatch.setattr(entry, "load_config", lambda *a, **kw: SimpleNamespace(state_dir="state", providers=[]))
    for name in ("Journal", "Git", "CommitLock", "SubprocessExec"):
        monkeypatch.setattr(entry, name, lambda *a, **kw: object())
    verdict = AsyncMock(return_value=0)
    monkeypatch.setattr(entry, "_verdict", verdict)
    for verb in ("confirm", "reject"):
        assert entry.main(["ticket", verb, "a", "--yes"], cwd=tmp_path, env={}) == 0
        assert verdict.await_args.args[1:3] == ("a", verb)
        assert verdict.await_args.args[4:] == (True, False)


def test_terminal_refusal_names_group(tmp_path, capsys):
    def reader(_):
        pytest.fail("terminal reader called")

    assert entry.main(["ticket", "confirm", "x"], cwd=tmp_path, env={}, terminal=(lambda: False, reader)) == 2
    output = capsys.readouterr()
    assert output.out == ""
    assert output.err == "clutch ticket: verdict requires an interactive terminal -- a human runs this in a terminal: `clutch ticket confirm|reject <stem>`\n"
