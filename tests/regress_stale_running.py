"""Carried reproducer for rejecting an interrupted run."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Standalone reproducer that checks `ticket reject` on an interrupted run ends with the ticket in the rejected state.
# relates: [clutch/__main__.py, clutch/journal.py, tests/integration/test_cli.py, tests/integration/test_drain.py]
# owner: engine
# verified: 7ad3c1c2
# hash: f35b8874adf19510e80e0251e20d8573fae3c8c0c435f69d47c414aa23be368f

import contextlib
import io
import json
import sys
import tempfile
import traceback
from pathlib import Path


def main():
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        from clutch.__main__ import main as clutch_main
        from clutch.journal import EventType
        from tests.cli_helpers import ENV
        from tests.drain_helpers import Clock, commit_ticket, confirmed, journal, make_root

        with tempfile.TemporaryDirectory() as directory:
            root = make_root(Path(directory))
            commit_ticket(root, "stale", confirmed())
            journal(root).append(EventType.STATE_TRANSITION, {"to": "running"}, ticket="stale")
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                result = clutch_main(["ticket", "reject", "--yes", "stale"], cwd=root, env=ENV, clock=Clock())
            states = [e.body["to"] for e in journal(root).read() if e.type == EventType.STATE_TRANSITION and e.ticket == "stale"]
            defect = result != 0 or states[-1] != "rejected"
    except Exception:
        traceback.print_exc(file=sys.stderr)
        print(json.dumps({"regression_result": "error"}))
        return 2
    print(json.dumps({"regression_result": "defect" if defect else "pass"}))
    return 1 if defect else 0


if __name__ == "__main__":
    sys.exit(main())
