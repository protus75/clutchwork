"""Run the held-Check composition regression and report its observed outcome."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Regression runner that runs the confirm-during-check integration test with pytest and reports pass, defect or error as JSON and as its exit code.
# relates: [tests/integration/test_serve_confirm_during_check.py]
# owner: engine
# verified: 8107f6ac
# hash: f129b76af93cbfb8b5cf421624a8a878ee5c6ff0524ee9d4cf7cdb80fc3ba33b

import json
import subprocess
import sys
from pathlib import Path

if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    test = root / "tests/integration/test_serve_confirm_during_check.py"
    try:
        if not test.is_file():
            raise FileNotFoundError(test)
        result = subprocess.run([sys.executable, "-m", "pytest", "-q", "-s", str(test) + "::test_confirmation_during_queued_merge_and_check"], cwd=root, capture_output=True, text=True, timeout=180)
        output = result.stdout + result.stderr
        status = "pass" if result.returncode == 0 else "defect" if "CONFIRM_NOT_APPLIED_WHILE_CHECK_HELD" in output and result.returncode == 1 else "error"
    except OSError, subprocess.TimeoutExpired:
        status = "error"
    print(json.dumps({"regression_result": status}))
    sys.exit(0 if status == "pass" else 1 if status == "defect" else 2)
