"""Carried reproducer for suggestions invisible until intake."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Standalone reproducer that checks `box suggest` puts a pending suggestion in the Suggestion Box straight away.
# relates: [clutch/box.py, clutch/seams.py, tests/integration/test_cli.py]
# owner: engine
# verified: ae1a5a3b
# hash: 8f239a24ae4d536c3630c43c603ecf5935edcd9702c0102462ef25aa1873abb2

import contextlib
import io
import json
import sys
import tempfile
import traceback
from pathlib import Path


def main() -> int:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    try:
        from clutch.box import Box
        from clutch.seams import LocalFileSystem
        from tests.cli_helpers import cli, root

        with tempfile.TemporaryDirectory() as directory:
            repo = root.__wrapped__(Path(directory))
            with contextlib.redirect_stdout(io.StringIO()):
                result = cli(repo, "box", "suggest", "a distinct idea")
            if result != 0:
                raise RuntimeError(f"suggest exited {result}")
            messages = Box(repo / ".clutch/state/box", LocalFileSystem()).messages()
            if not any(m.message_class == "suggestion" and m.status == "pending" and m.summary == "a distinct idea" for m in messages):
                print(json.dumps({"regression_result": "defect"}))
                return 1
    except BaseException:
        traceback.print_exc(file=sys.stderr)
        print(json.dumps({"regression_result": "error"}))
        return 2
    print(json.dumps({"regression_result": "pass"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
