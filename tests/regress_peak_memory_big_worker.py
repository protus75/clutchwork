"""Reproduce peak-memory measurements from a large pytest worker."""

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
