# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test visual baseline dev
# relates: [dev.py]
# owner: dev.py
# verified: 96e46658
# hash: 534d4437edbf6b14bd5b4b1e21313bb693c1aa45b71b4c1ff3ba704774ca3793
from unittest.mock import Mock

import pytest

import dev


def test_visual_baseline_command(monkeypatch):
    monkeypatch.setattr(dev.sys, "argv", ["dev.py", "visual-baseline"])
    run = Mock(return_value=Mock(returncode=4))
    monkeypatch.setattr(dev.subprocess, "run", run)
    with pytest.raises(SystemExit) as error:
        dev.main()
    assert error.value.code == 4
    run.assert_called_once_with(["uv", "run", "python", "-m", "eval.visual_harness", "run"], cwd=dev.ROOT, check=False)
