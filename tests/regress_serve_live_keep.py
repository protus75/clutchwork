"""Carried reproducer for a keep racing a serve re-offer."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Carried regression reproducer: runs test_runner_verdict_reread.py under pytest and prints a pass/defect/error regression_result JSON for a keep racing a serve re-offer.
# relates: [tests/unit/test_runner_verdict_reread.py]
# owner: engine
# verified: 6a73a3c1
# hash: 657a400028653b917389201553333bcbe85ac5189f84441d5048040b19b6fcfd

import json
import subprocess
import sys
import traceback
from pathlib import Path


def main() -> int:
    try:
        root = Path(__file__).resolve().parents[1]
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "-n0", "tests/unit/test_runner_verdict_reread.py"],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
        code = result.returncode if result.returncode in (0, 1) else 2
    except Exception:
        traceback.print_exc(file=sys.stderr)
        code = 2
    print(json.dumps({"regression_result": {0: "pass", 1: "defect", 2: "error"}[code]}))
    return code


if __name__ == "__main__":
    sys.exit(main())
