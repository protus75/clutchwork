"""Reproduce the roadmap follow-up row failure."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Reproduce the roadmap follow-up row failure.
# relates: []
# owner: engine
# verified: d7719818
# hash: 79822b0174cb7a2c74c9257c05926a6204da41bc69f64b0332ac3633521dbb3e

import json
import subprocess
import sys
import traceback
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "tests/integration/test_closed_sets_single_owner.py::test_follow_up_row"],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
        sys.stderr.write(result.stdout + result.stderr)
        outcome, code = {0: ("pass", 0), 1: ("defect", 1)}.get(result.returncode, ("error", 2))
    except Exception:
        traceback.print_exc(file=sys.stderr)
        outcome, code = "error", 2
    print(json.dumps({"regression_result": outcome}))
    return code


if __name__ == "__main__":
    sys.exit(main())
