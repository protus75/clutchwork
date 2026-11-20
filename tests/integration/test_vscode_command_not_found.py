"""Exercise errors from the VS Code extension's snapshot command."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Exercise errors from the VS Code extension's snapshot command.
# relates: []
# owner: engine
# verified: 96e46658
# hash: f1c4df3d1cb535dea42a4bcdb297a6676596b178d14017c8d893ef069f66a076

import json
import subprocess
from pathlib import Path

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
