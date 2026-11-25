# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Tests the `clutch engine serve --detach` CLI path: parser flag, spawn argv with optional --config, startup wait outcomes (success, timeout, refusal), and no spawn on invalid config.
# relates: [clutch/__main__.py, clutch/runner.py, clutch/serve.py]
# owner: engine
# verified: 135c51d4
# hash: f97a4a7f5e3261060a0fd3f658eff7e4fde5af0121d37139268f0eeea192686d
import sys
from types import SimpleNamespace
from unittest.mock import Mock

from clutch import runner, serve
from clutch.__main__ import _parser, main


def test_parser():
    assert _parser().parse_args(["engine", "serve"]).detach is False
    assert _parser().parse_args(["engine", "serve", "--detach"]).detach is True


def test_detach(tmp_path, monkeypatch, capsys):
    state = tmp_path / "state"
    monkeypatch.setattr("clutch.__main__.load_config", lambda *a, **k: SimpleNamespace(state_dir=state))
    baseline = Mock(return_value=(15, "old"))
    wait = Mock(return_value=True)
    monkeypatch.setattr(serve, "capture_startup_baseline", baseline)
    monkeypatch.setattr(serve, "wait_detached_startup", wait)
    spawn = Mock(return_value=4242)
    env = {"PATH": "example"}
    output = state / "serve.out"
    assert main(["engine", "serve", "--detach"], cwd=tmp_path, env=env, spawn=spawn) == 0
    spawn.assert_called_once_with([sys.executable, "-m", "clutch", "engine", "serve"], cwd=tmp_path, env=env, output=output)
    baseline.assert_called_once_with(state, output)
    wait.assert_called_once_with(state, 4242, output, prior_size=15, prior_lifecycle="old")
    assert capsys.readouterr().out == f"serve: pid 4242, output {output}\n"
    spawn.reset_mock()
    cfg = tmp_path / "custom.yaml"
    assert main(["--config", str(cfg), "engine", "serve", "--detach"], cwd=tmp_path, env=env, spawn=spawn) == 0
    spawn.assert_called_once_with([sys.executable, "-m", "clutch", "--config", str(cfg), "engine", "serve"], cwd=tmp_path, env=env, output=output)
    capsys.readouterr()
    wait.return_value = False
    assert main(["engine", "serve", "--detach"], cwd=tmp_path, env=env, spawn=spawn) == 2
    out = capsys.readouterr()
    assert out.out == "" and "startup timed out" in out.err
    wait.side_effect = runner.Refusal("broken", "repair it")
    assert main(["engine", "serve", "--detach"], cwd=tmp_path, env=env, spawn=spawn) == 2
    out = capsys.readouterr()
    assert out.out == "" and out.err == "clutch engine: broken -- repair it\n"


def test_invalid_config_does_not_spawn(tmp_path, capsys):
    spawn = Mock()
    assert main(["engine", "serve", "--detach"], cwd=tmp_path, env={}, spawn=spawn) == 2
    spawn.assert_not_called()
    assert "config file not found" in capsys.readouterr().err
