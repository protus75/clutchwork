"""Carried reproducer for load-sensitive testguard duration ordering."""

import json
import os
import subprocess
import sys
import traceback
from pathlib import Path


def main() -> int:
    try:
        root = Path(__file__).resolve().parents[1]
        env = os.environ.copy()
        env["PYTHONPATH"] = str(root / "tests" / "regress_sleep_skew")
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "-o", "addopts=", "tests/integration/test_testguard.py::test_budget_and_slowest"],
            cwd=root,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode not in (0, 1):
            raise RuntimeError(f"pytest exited {result.returncode}:\n{result.stdout}\n{result.stderr}")
        defect = result.returncode == 1
    except Exception:
        traceback.print_exc(file=sys.stderr)
        print(json.dumps({"regression_result": "error"}))
        return 2
    print(json.dumps({"regression_result": "defect" if defect else "pass"}))
    return 1 if defect else 0


if __name__ == "__main__":
    sys.exit(main())
