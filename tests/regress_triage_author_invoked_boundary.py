"""Carried reproducer for the triage author invocation boundary across a self-upgrade."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Carried reproducer for the triage author invocation boundary across a self-upgrade.
# relates: []
# owner: engine
# verified: d7719818
# hash: e6c8d39c0ae93467b2dd20a78a41696a96f040d1d3627d52ca1bb71d48dcd3e3

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
            result = pytest.main(["tests/integration/test_triage.py", "-k", "stale_author_invoked", "-q", "-p", "no:cacheprovider"])
        verdict, code = {0: ("pass", 0), 1: ("defect", 1)}.get(result, ("error", 2))
    except BaseException:
        traceback.print_exc(file=sys.stderr)
        verdict, code = "error", 2
    print(json.dumps({"regression_result": verdict}))
    return code


if __name__ == "__main__":
    sys.exit(main())
