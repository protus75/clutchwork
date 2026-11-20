"""Carried reproducer for infra re-offers consuming retry."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Carried reproducer for infra re-offers consuming retry.
# relates: []
# owner: engine
# verified: d7719818
# hash: fd31f0cddff0dac3f3214445ed253bd42b1a99bcdc33f62f912f5d966af71f35

import contextlib
import json
import sys
import traceback


def main() -> int:
    try:
        import pytest

        with contextlib.redirect_stdout(sys.stderr):
            result = pytest.main(["tests/unit/test_drain_reoffer.py", "-k", "infra_error", "-q", "-p", "no:cacheprovider"])
        verdict, code = {0: ("pass", 0), 1: ("defect", 1)}.get(result, ("error", 2))
    except BaseException:
        traceback.print_exc(file=sys.stderr)
        verdict, code = "error", 2
    print(json.dumps({"regression_result": verdict}))
    return code


if __name__ == "__main__":
    sys.exit(main())
