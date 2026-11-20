# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test drain detach cli
# relates: [clutch/__main__.py]
# owner: clutch/__main__.py
# verified: 0a308920
# hash: debb31fe53c661ca55cc90a0b20fec4b002d290da524a4e4d64ec9ab6e92fca8
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

from clutch.__main__ import main


def test_drain_detach_spawns_and_returns(monkeypatch, capsys):
    monkeypatch.setattr("clutch.__main__.load_config", lambda *args, **kwargs: SimpleNamespace(state_dir=Path("/state")))
    spawn = Mock(return_value=4242)
    assert main(["engine", "drain", "--detach"], cwd=Path("/repo"), env={}, spawn=spawn) == 0
    spawn.assert_called_once_with([sys.executable, "-m", "clutch", "engine", "drain"], cwd=Path("/repo"), env={}, output=Path("/state/drain.out"))
    assert capsys.readouterr().out == "drain: pid 4242, output /state/drain.out\n"
