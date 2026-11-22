"""Carried reproducer for drain detachment at the engine verb."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Standalone reproducer that checks `engine drain --detach` spawns one detached process and exits 0.
# relates: [clutch/__main__.py, tests/integration/test_cli.py, tests/integration/test_drain.py]
# owner: engine
# verified: ae1a5a3b
# hash: b75f0013f52e0c9ac5aa1ee075e740f627db338806aec9ce4d51ccd0dfc022b9

import contextlib
import io
import json
import sys
import tempfile
import traceback
from pathlib import Path
from unittest.mock import Mock


def main() -> int:
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        from clutch.__main__ import _parser
        from clutch.__main__ import main as clutch_main
        from tests.cli_helpers import ENV
        from tests.integration.test_drain import make_root

        with tempfile.TemporaryDirectory() as directory:
            root = make_root(Path(directory))
            spawn = Mock(return_value=4242)
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    _parser().parse_args(["engine", "drain", "--detach"])
                    result = clutch_main(["engine", "drain", "--detach"], cwd=root, env=ENV, spawn=spawn)
                defect = result != 0 or spawn.call_count != 1
            except SystemExit:
                defect = True
    except Exception:
        traceback.print_exc(file=sys.stderr)
        print(json.dumps({"regression_result": "error"}))
        return 2
    print(json.dumps({"regression_result": "defect" if defect else "pass"}))
    return 1 if defect else 0


if __name__ == "__main__":
    sys.exit(main())
