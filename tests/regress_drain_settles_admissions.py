"""Carried reproducer for drain admission settlement."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Carried reproducer for drain admission settlement.
# relates: []
# owner: engine
# verified: d7719818
# hash: 23ba991cf5d5a4e973432105f40db962d66d365a000b80b1a3ef133c58094670

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
            result = pytest.main(["tests/integration/test_drain_admissions.py", "-q", "-p", "no:cacheprovider"])
        verdict, code = {0: ("pass", 0), 1: ("defect", 1)}.get(result, ("error", 2))
    except BaseException:
        traceback.print_exc(file=sys.stderr)
        verdict, code = "error", 2
    print(json.dumps({"regression_result": verdict}))
    return code


if __name__ == "__main__":
    sys.exit(main())
