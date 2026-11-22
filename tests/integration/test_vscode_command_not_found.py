"""Exercise errors from the VS Code extension's snapshot command."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Runs the node harness to check the VS Code extension's error message when the snapshot command is missing and when it fails for another reason
# relates: [tests/vscode_command_not_found.js, vscode-clutchwork/package.json]
# owner: vscode-clutchwork
# verified: d32c32ad
# hash: dc66401d39372cb067de092e2286719731c02f357ad7120c7317e92a394a9db9

import json
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.disk_io_skip

HARNESS = Path(__file__).parents[1] / "vscode_command_not_found.js"


def run_snapshot(tmp_path, binary):
    (tmp_path / "tickets").mkdir()
    result = subprocess.run(
        ["node", str(HARNESS), str(tmp_path), binary],
        capture_output=True,
        text=True,
        check=True,
        timeout=10,
    )
    return json.loads(result.stdout)


def test_missing_command_names_setting_and_workspace(tmp_path):
    message = run_snapshot(tmp_path, ".venv/bin/clutch-missing")
    assert message == (f"clutch command not found: .venv/bin/clutch-missing (run from {tmp_path}). Set clutch.command in settings.")


def test_other_command_failure_keeps_its_message(tmp_path):
    message = run_snapshot(tmp_path, "false")
    assert "clutch command not found" not in message
    assert "false" in message
