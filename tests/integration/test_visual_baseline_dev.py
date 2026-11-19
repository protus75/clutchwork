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
