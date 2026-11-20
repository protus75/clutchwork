"""Carried reproducer for suggestions invisible until intake."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Carried reproducer for suggestions invisible until intake.
# relates: [clutch/box.py, clutch/seams.py, tests/integration/test_cli.py]
# owner: engine
# verified: d7719818
# hash: 7275df5adbcbc74d0967e88b624497d114cce04d6a71c26c7a8f7c7a60564256

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
        from tests.integration.test_cli import cli, root

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
