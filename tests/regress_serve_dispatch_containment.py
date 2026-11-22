"""Carried reproducer for serve dispatch exception containment."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Bug regression script that runs the serve dispatch containment unit tests and prints a pass/defect/error regression_result JSON verdict
# relates: [tests/unit/test_serve_dispatch_containment.py]
# owner: engine
# verified: 33066275
# hash: 22b04cc2c73327f6ad3e198336338de4d1230da7db58f12709f8d3dba2281da0

import contextlib
import json
import sys
import traceback
from pathlib import Path


def main() -> int:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    try:
        import pytest

        with contextlib.redirect_stdout(sys.stderr):
            result = pytest.main(["tests/unit/test_serve_dispatch_containment.py", "-k", "raises", "-q", "-p", "no:cacheprovider"])
        verdict, code = {0: ("pass", 0), 1: ("defect", 1)}.get(result, ("error", 2))
    except BaseException:
        traceback.print_exc(file=sys.stderr)
        verdict, code = "error", 2
    print(json.dumps({"regression_result": verdict}))
    return code


if __name__ == "__main__":
    sys.exit(main())
