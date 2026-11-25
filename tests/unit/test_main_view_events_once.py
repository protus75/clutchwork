# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Unit tests for the `clutch view events --once` CLI: option parsing, JSON output and default seams, argument refusals, and quiet interrupt handling.
# relates: [clutch/__main__.py, clutch/events.py]
# owner: engine
# verified: bdb23dbf
# hash: 051e17501341d289579ff752a844f0cfd38dc00b07684a9bd8c4dadf82327585
import json
from types import SimpleNamespace

import pytest

from clutch import __main__ as entry
from clutch import events


def test_parser():
    args = entry._parser().parse_args(["view", "events", "--once", "--cursor", "tok", "--timeout", "15"])
    assert (args.once, args.cursor, args.timeout) == (True, "tok", 15.0)  # Ignoring or misparsing an option differs.


def test_once(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(entry, "load_config", lambda *a, **kw: SimpleNamespace(state_dir=tmp_path, providers=[]))
    calls = []

    def wait(state, **kwargs):
        calls.append((state, kwargs))
        return "next", ["event"], False

    monkeypatch.setattr(events, "wait_once", wait)
    assert entry.main(["view", "events", "--once"], cwd=tmp_path, env={}) == 0
    output = capsys.readouterr()
    assert json.loads(output.out) == {"cursor": "next", "events": ["event"], "timed_out": False} and output.out.count("\n") == 1 and output.err == ""  # Wrong output or extra lines differ.
    assert calls[0][0] == tmp_path and calls[0][1] == {"cursor": None, "timeout": 300.0, "sleep": entry.time.sleep, "clock": entry.time.monotonic}  # Wrong defaults or seams differ.


@pytest.mark.parametrize("args", [["--cursor", "tok"], ["--timeout", "10"], ["--once", "--cursor", "invalid"], ["--once", "--timeout", "-1"]])
def test_refusal(tmp_path, monkeypatch, capsys, args):
    monkeypatch.setattr(entry, "load_config", lambda *a, **kw: SimpleNamespace(state_dir=tmp_path, providers=[]))
    monkeypatch.setattr(events, "stream", lambda *a, **kw: None)
    assert entry.main(["view", "events", *args], cwd=tmp_path, env={}) == 2  # Accepting invalid arguments differs.
    output = capsys.readouterr()
    assert output.err.startswith("clutch view: ") and output.out == ""  # Traceback or output on success differs.


def test_interrupt(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(entry, "load_config", lambda *a, **kw: SimpleNamespace(state_dir=tmp_path, providers=[]))

    def stop(*a, **kw):
        raise KeyboardInterrupt

    monkeypatch.setattr(events, "wait_once", stop)
    assert entry.main(["view", "events", "--once"], cwd=tmp_path, env={}) == 0  # Propagating interruption differs.
    assert capsys.readouterr().err == ""  # Printing an error differs.
