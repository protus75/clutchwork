# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Tests that an OS signal stops a running drain the same way an accepted kill request does, journals the kill, and restores the signal handlers.
# relates: [clutch/__main__.py, clutch/llm.py, clutch/runner.py, tests/integration/test_cli.py, tests/integration/test_drain.py]
# owner: engine
# verified: 0a4d026b
# hash: a660e8c1ca4f486a52e921b472d87df44dd0b40b071a295a4311bcfd8d98702c
import asyncio
import json

import pytest

from clutch import __main__ as cli
from clutch import runner
from clutch.llm import FakeLLM
from tests.cli_helpers import ENV
from tests.drain_helpers import Clock, commit_ticket, confirmed, journal, root
from tests.stages_helpers import agent

pytestmark = pytest.mark.disk_io_skip


def test_signal_kills_a_running_drain_like_kill(root, monkeypatch, capsys):
    commit_ticket(root, "work", confirmed())
    callbacks, restored, life = [], [], []

    def signals(callback):
        callbacks.append(callback)
        return lambda: restored.append(True)

    monkeypatch.setattr(cli, "_engine_signals", signals)

    class Blocking(FakeLLM):
        async def call(self, req):
            callbacks[0]()
            await asyncio.Event().wait()

    def pipeline(checkout):
        life.append(checkout.control.inbox.lifecycle_id)
        return runner.bind(checkout, Blocking([agent({}, outcome="already_satisfied")]))

    assert cli.main(["engine", "drain"], cwd=root, env=ENV, clock=Clock(), pipeline=pipeline) == runner.EXIT_TICKET
    assert "drain stopped by kill -- NOT quiescent" in capsys.readouterr().out
    events = [json.loads(line) for line in (root / ".clutch/state/engine.log").read_text().splitlines()]
    assert any(e["event"] == "engine_stop" and e["verb"] == "drain" and e["outcome"] == "killed" for e in events)
    assert any(
        e.body.get("kind") == "control_decision" and e.body.get("verb") == "kill" and e.body.get("decision") == "accepted" and e.body.get("lifecycle_id") == life[0] for e in journal(root).read()
    )
    assert restored == [True]
