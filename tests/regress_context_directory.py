"""Carried reproducer for a directory accepted as ticket Context."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Carried reproducer for a directory accepted as ticket Context.
# relates: [clutch/tickets.py, tests/integration/test_tickets.py]
# owner: engine
# verified: d7719818
# hash: 5d38aeea0d3bd121163051ac51cbc3f9a8ea9b1a658de356edbf002119983439

import json
import sys
import tempfile
import traceback
from pathlib import Path


def main() -> int:
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        from clutch.tickets import TicketInvalid, validate_ticket
        from tests.integration.test_tickets import VALID, complete

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "context-dir").mkdir()
            text = complete(VALID.replace("clutch/thing.py\n\n## Goal", "context-dir\n\n## Goal"))
            try:
                validate_ticket("t-one", text, root)
            except TicketInvalid as exc:
                if not any("Context" in finding.message for finding in exc.findings):
                    raise
                outcome, code = "pass", 0
            else:
                outcome, code = "defect", 1
    except Exception:
        traceback.print_exc(file=sys.stderr)
        outcome, code = "error", 2
    print(json.dumps({"regression_result": outcome}))
    return code


if __name__ == "__main__":
    sys.exit(main())
