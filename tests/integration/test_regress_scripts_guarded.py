"""Regression scripts are inert when imported and remain executable."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Regression scripts are inert when imported and remain executable.
# relates: []
# owner: engine
# verified: 96e46658
# hash: 1d159f8ccdde0e352a791e200d9ddb8c3c82ce15f1d36d75a0c467684b1c69b0

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = sorted((ROOT / "tests").glob("regress_*.py"))


def test_regression_scripts_are_guarded(capsys):
    assert SCRIPTS
    for script in SCRIPTS:
        assert 'if __name__ == "__main__":' in script.read_text(), script.name
        spec = importlib.util.spec_from_file_location(script.stem, script)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        assert capsys.readouterr().out == "", script.name


def test_premise_park_script_runs():
    result = subprocess.run(
        [sys.executable, "tests/regress_premise_park_keep.py"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert result.stdout.splitlines() == ['{"regression_result": "pass"}']
    assert json.loads(result.stdout) == {"regression_result": "pass"}
