"""Carried reproducer for watch surface capability display."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Carried reproducer for watch surface capability display.
# relates: []
# owner: engine
# verified: d7719818
# hash: 5674e27927dcddabba15179cb25fd7aa1a3d0647f1ab82001d88e1b8832ad48f

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
            result = pytest.main(["tests/integration/test_watch_surface_tier.py", "-q", "-p", "no:cacheprovider"])
        verdict, code = {0: ("pass", 0), 1: ("defect", 1)}.get(result, ("error", 2))
    except BaseException:
        traceback.print_exc(file=sys.stderr)
        verdict, code = "error", 2
    print(json.dumps({"regression_result": verdict}))
    return code


if __name__ == "__main__":
    sys.exit(main())
