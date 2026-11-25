# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Unit-tests detached serve startup helpers: child exit polling, startup baseline capture, lock/lifecycle confirmation, wait loop timing, refusals, timeout and argument validation.
# relates: [clutch/runner.py, clutch/seams.py, clutch/serve.py]
# owner: engine
# verified: 135c51d4
# hash: 8b3c6519221722c8db0bbd509054f11514c7b50e054639af611fc14845410ab3
import json
import os
from unittest.mock import Mock

import pytest

from clutch import runner, seams, serve


def publish(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


def test_child_exit(monkeypatch):
    wait = Mock(return_value=(0, 0))
    monkeypatch.setattr(os, "waitpid", wait)
    assert seams.child_exit(123) is None
    wait.assert_called_with(123, os.WNOHANG)
    wait.return_value = (123, 2 << 8)
    assert seams.child_exit(123) == 2
    wait.side_effect = ChildProcessError
    assert seams.child_exit(123) is None


def test_baseline_and_confirmation(tmp_path):
    output = tmp_path / "serve.out"
    assert serve.capture_startup_baseline(tmp_path, output) == (0, None)
    output.write_text("old output")
    active = tmp_path / "control/active.json"
    lock = tmp_path / "clutch.lock"
    publish(active, {"lifecycle_id": "old"})
    assert serve.capture_startup_baseline(tmp_path, output) == (10, "old")
    assert not serve.startup_confirmed(tmp_path, 42, "old")
    for identity, lifecycle in [
        ({"pid": 43, "verb": "serve"}, "fresh"),
        ({"pid": 42, "verb": "drain"}, "fresh"),
        ({"pid": 42, "verb": "serve"}, None),
        ({"pid": 42, "verb": "serve"}, "old"),
        ({"pid": 42, "verb": "serve"}, ""),
    ]:
        publish(lock, identity)
        publish(active, None if lifecycle is None else {"lifecycle_id": lifecycle})
        assert not serve.startup_confirmed(tmp_path, 42, "old")
    publish(active, {"lifecycle_id": "fresh"})
    assert serve.startup_confirmed(tmp_path, 42, "old")


def test_wait_confirmed_and_delayed(tmp_path, monkeypatch):
    confirmed = Mock(side_effect=[True, False, True])
    monkeypatch.setattr(serve, "startup_confirmed", confirmed)
    now = [0.0]

    def advance(delay):
        now[0] += delay

    sleep = Mock(side_effect=advance)
    poll = Mock(return_value=None)
    assert serve.wait_detached_startup(tmp_path, 42, tmp_path / "out", sleep=sleep, poll_child=poll, clock=lambda: now[0])
    sleep.assert_not_called()
    assert serve.wait_detached_startup(tmp_path, 42, tmp_path / "out", sleep=sleep, poll_child=poll, clock=lambda: now[0])
    sleep.assert_called_once_with(0.05)
    poll.assert_called_once_with(42)


def test_wait_refusals(tmp_path):
    output = tmp_path / "out"
    output.write_text("old refusal\nclutch engine: broken -- repair it\n")
    with pytest.raises(runner.Refusal, match="^broken -- repair it$"):
        serve.wait_detached_startup(tmp_path, 42, output, prior_size=len("old refusal\n"), poll_child=lambda pid: 2)
    for code in (0, 1):
        with pytest.raises(runner.Refusal, match=f"exited {code}"):
            serve.wait_detached_startup(tmp_path, 42, output, prior_size=output.stat().st_size, poll_child=lambda pid: code)


def test_wait_timeout_and_validation(tmp_path):
    now = [0.0]
    sleeps = []
    polls = []

    def sleep(delay):
        sleeps.append(delay)
        now[0] += delay

    def poll(pid):
        polls.append(pid)
        return None

    assert not serve.wait_detached_startup(tmp_path, 42, tmp_path / "out", clock=lambda: now[0], sleep=sleep, poll_child=poll, timeout=0.12, interval=0.05)
    assert sleeps == pytest.approx([0.05, 0.05, 0.02])
    assert polls == [42, 42, 42, 42]
    for kwargs in ({"timeout": -1}, {"timeout": float("nan")}, {"interval": 0}, {"interval": float("inf")}):
        with pytest.raises(ValueError):
            serve.wait_detached_startup(
                tmp_path, 42, tmp_path / "out", clock=lambda: 0, sleep=Mock(side_effect=RuntimeError("unexpected sleep")), poll_child=lambda _: None, **({"timeout": 0} | kwargs)
            )
