# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test dev testguard
# relates: [dev.py]
# owner: dev.py
# verified: 0a308920
# hash: ed4430a52b1203e79ab71aebb8f431ca63d00984336411d79b6cc0df527bcda9
from unittest.mock import Mock, call

import pytest

import dev


@pytest.mark.parametrize("argv", [["dev.py"], ["dev.py", "test"]])
def test_suite_runs_unit_guarded_then_integration(monkeypatch, argv):
    monkeypatch.setattr(dev.sys, "argv", argv)
    runner = Mock(return_value=Mock(returncode=0))
    monkeypatch.setattr(dev.subprocess, "run", runner)
    dev.main()
    assert runner.call_args_list == [
        call(["uv", "run", "pytest", "-q", "-p", "clutch.testguard", "tests/unit"], cwd=dev.ROOT, check=False),
        call(["uv", "run", "pytest", "-q", "tests/integration"], cwd=dev.ROOT, check=False),
    ]  # Reject a single run, a guarded whole tree, or guarded integration.


def test_unit_failure_stops_before_integration(monkeypatch):
    monkeypatch.setattr(dev.sys, "argv", ["dev.py", "test"])
    runner = Mock(return_value=Mock(returncode=1))
    monkeypatch.setattr(dev.subprocess, "run", runner)
    with pytest.raises(SystemExit) as error:
        dev.main()
    assert error.value.code is not None and error.value.code != 0  # Failure must not exit successfully.
    assert runner.call_args_list == [call(["uv", "run", "pytest", "-q", "-p", "clutch.testguard", "tests/unit"], cwd=dev.ROOT, check=False)]  # Integration must not start.


@pytest.mark.parametrize("args", [["tests/unit"], ["tests/unit/test_graph.py::test_x", "-k", "foo"], ["-k", "foo", "tests/unit/test_a.py", "tests/unit/test_b.py"]])
def test_unit_paths_load_testguard(monkeypatch, args):
    monkeypatch.setattr(dev.sys, "argv", ["dev.py", "test", *args])
    runner = Mock(return_value=Mock(returncode=0))
    monkeypatch.setattr(dev.subprocess, "run", runner)
    dev.main()
    runner.assert_called_once_with(["uv", "run", "pytest", "-q", "-p", "clutch.testguard", *args], cwd=dev.ROOT, check=False)  # Guard every unit path and preserve argv order.


@pytest.mark.parametrize("args", [["tests/integration"], ["tests"], ["tests/unit/test_a.py", "tests/integration/test_b.py"], ["-k", "foo"], ["--durations=25"]])
def test_other_paths_run_unguarded(monkeypatch, args):
    monkeypatch.setattr(dev.sys, "argv", ["dev.py", "test", *args])
    runner = Mock(return_value=Mock(returncode=0))
    monkeypatch.setattr(dev.subprocess, "run", runner)
    dev.main()
    runner.assert_called_once_with(["uv", "run", "pytest", "-q", *args], cwd=dev.ROOT, check=False)  # Never guard integration or alter option-only argv.
