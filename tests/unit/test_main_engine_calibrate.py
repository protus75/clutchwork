import argparse
from types import SimpleNamespace

import pytest

import clutch.__main__ as cli
from clutch.config import Calibration
from clutch.journal import EventType, Journal
from tests.fakes import FakeClock


def test_calibrate_is_an_engine_subcommand():
    parser = cli._parser()
    assert parser.parse_args(["engine", "calibrate"]).engine_verb == "calibrate"
    choices = next(a for a in parser._actions if isinstance(a, argparse._SubParsersAction)).choices
    assert "calibrate" not in choices
    for args in (["calibrate"], ["engine", "calibrate", "extra"]):
        with pytest.raises(SystemExit) as exc:
            parser.parse_args(args)
        assert exc.value.code == 2


def test_main_calibrate_journals_and_prints(tmp_path, monkeypatch, capsys):
    clock = FakeClock()
    journal = Journal(tmp_path / "state", clock)
    key = "llm/a/1/implement/1/1"
    journal.append(EventType.EFFECT_INTENT, {}, key=key)
    clock.advance(240)
    journal.append(EventType.EFFECT_COMPLETION, {"cost": {"provider": "codex", "model": "m1"}}, key=key)
    ticket = tmp_path / "tickets/a/ticket.md"
    ticket.parent.mkdir(parents=True)
    ticket.write_text("- expected: 30m\n")
    monkeypatch.setattr(cli, "load_config", lambda *a, **kw: SimpleNamespace(state_dir=tmp_path / "state", calibration=Calibration(every=7)))
    monkeypatch.setattr(cli, "child_env", lambda *a: {})

    def fail_lock(*args, **kwargs):
        raise AssertionError("writer lock taken")

    monkeypatch.setattr(cli, "Lockfile", fail_lock)
    assert cli.main(["engine", "calibrate"], cwd=tmp_path, env={}, clock=clock) == 0
    assert capsys.readouterr().out == "codex/m1: 1 runs, estimate p50 30.0m, actual p50 4.0m, actual p90 4.0m\n"
    assert journal.read()[-1].body == {
        "signal": "estimate_calibration",
        "window": 7,
        "rows": [{"provider": "codex", "model": "m1", "runs": 1, "expected_p50": 30.0, "actual_p50": 4.0, "actual_p90": 4.0}],
    }
