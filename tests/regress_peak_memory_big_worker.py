"""Reproduce peak-memory measurements from a large pytest worker."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Reproduce peak-memory measurements from a large pytest worker.
# relates: []
# owner: engine
# verified: d7719818
# hash: 2c6b2497fa5f48b20b95d5a135b43d7d9df756baefa0ad94f0c60055d8e2f951

import contextlib
import json
import sys
import traceback


def main() -> int:
    try:
        import pytest

        memory = b"\x01" * 600_000_000
        with contextlib.redirect_stdout(sys.stderr):
            result = pytest.main(["-n0", "-q", "tests/integration/test_exec_seam_reap.py::test_usage_and_independent_peak_memory"])
        if result == pytest.ExitCode.OK:
            outcome, code = "pass", 0
        elif result == pytest.ExitCode.TESTS_FAILED:
            outcome, code = "defect", 1
        else:
            outcome, code = "error", 2
        del memory
    except Exception:
        traceback.print_exc(file=sys.stderr)
        outcome, code = "error", 2
    print(json.dumps({"regression_result": outcome}))
    return code


if __name__ == "__main__":
    sys.exit(main())
