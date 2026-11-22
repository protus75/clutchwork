"""Snapshot drawing errors remain visible in each extension view."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Tests through a node harness that each VS Code extension view shows snapshot draw errors with setup help and that the extension README explains how to update
# relates: [tests/vscode_draw_failure.js, vscode-clutchwork/README.md]
# owner: engine
# verified: d32c32ad
# hash: 23e5a08cf09c909b57be8a6257967c6393bcb4df8df639da191bcb1dce368954

import json
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.disk_io_skip

ROOT = Path(__file__).resolve().parents[2]
HARNESS = ROOT / "tests/vscode_draw_failure.js"


def draw(view, scenario):
    result = subprocess.run(["node", str(HARNESS), view, scenario], capture_output=True, text=True, check=True, timeout=10)
    return json.loads(result.stdout)


@pytest.mark.parametrize("view", ["view", "box", "detail"])
def test_unreadable_snapshot_reports_error_and_help(view):
    result = draw(view, "invalid")
    assert result["text"].startswith("cannot draw the clutch snapshot: ")
    assert "undefined" in result["text"]
    assert result["text"].endswith("Open setup help")
    assert result["message"] == {"type": "readme"}


@pytest.mark.parametrize("view", ["view", "box"])
def test_snapshot_command_error_remains_visible(view):
    result = draw(view, "error")
    assert result["text"].startswith("snapshot failed: boom")
    assert result["message"] == {"type": "readme"}


@pytest.mark.parametrize("view", ["view", "box", "detail"])
def test_valid_snapshot_draws(view):
    result = draw(view, "valid")
    assert "cannot draw the clutch snapshot" not in result["text"]
    if view == "detail":
        assert result["text"].startswith("Nothing running.")
    elif view == "view":
        assert result["text"].startswith("engine ")
    else:
        assert result["text"] == ""


def test_readme_explains_extension_update():
    readme = (ROOT / "vscode-clutchwork/README.md").read_text()
    assert "cannot draw the clutch snapshot" in readme
    assert "Marketplace" in readme
    assert "reload the window" in readme
    assert "./dev.py" not in readme
