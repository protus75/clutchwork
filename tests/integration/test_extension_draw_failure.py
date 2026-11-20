"""Snapshot drawing errors remain visible in each extension view."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Snapshot drawing errors remain visible in each extension view.
# relates: []
# owner: engine
# verified: 148a8874
# hash: 1a46d8636b689ff83c8da55866ac4322fffbb85f41546a8a4606a0d12c60228a

import json
import subprocess
from pathlib import Path

import pytest

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
