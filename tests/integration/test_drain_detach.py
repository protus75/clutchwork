# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test drain detach
# relates: [clutch/__main__.py, clutch/seams.py, tests/integration/test_cli.py, tests/integration/test_drain.py]
# owner: engine
# verified: 148a8874
# hash: b3792d5469b95a341a4b17054843e358b852bde554b5fbcf8825abd57c192de9
import os
import sys
from unittest.mock import Mock

from clutch.__main__ import main
from clutch.seams import spawn_detached
from tests.integration.test_cli import ENV
from tests.integration.test_drain import make_root


def test_detach_spawns_a_foreground_drain_and_returns(tmp_path, capsys):
    root = make_root(tmp_path)
    spawn = Mock(return_value=4242)
    output = root / ".clutch/state/drain.out"
    assert main(["engine", "drain", "--detach"], cwd=root, env=ENV, spawn=spawn) == 0
    spawn.assert_called_once_with([sys.executable, "-m", "clutch", "engine", "drain"], cwd=root, env=ENV, output=output)
    assert capsys.readouterr().out == f"drain: pid 4242, output {output}\n"
    log = root / ".clutch/state/engine.log"
    assert not log.exists() or "engine_start" not in log.read_text()


def test_detach_forwards_config(tmp_path):
    root = make_root(tmp_path)
    config = root / "config.yaml"
    spawn = Mock(return_value=4242)
    assert main(["--config", str(config), "engine", "drain", "--detach"], cwd=root, env=ENV, spawn=spawn) == 0
    spawn.assert_called_once_with([sys.executable, "-m", "clutch", "--config", str(config), "engine", "drain"], cwd=root, env=ENV, output=root / ".clutch/state/drain.out")


def test_spawn_detached_runs_in_its_own_session_and_appends(tmp_path):
    output = tmp_path / "drain.out"
    output.write_text("before\n")
    pid = spawn_detached([sys.executable, "-c", "import os; print(os.getsid(0) == os.getpid())"], cwd=tmp_path, env=os.environ, output=output)
    _, status = os.waitpid(pid, 0)
    assert os.waitstatus_to_exitcode(status) == 0
    assert output.read_text() == "before\nTrue\n"
