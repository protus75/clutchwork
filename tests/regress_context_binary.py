"""Carried reproducer for a binary file accepted as ticket Context."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Carried reproducer for a binary file accepted as ticket Context.
# relates: [clutch/tickets.py, tests/integration/test_tickets.py]
# owner: engine
# verified: d7719818
# hash: 2d917572b843ceeea9991323e5f0d6bd43c299e68dcb5b592dffdf4565f964f5

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
            (root / "image.png").write_bytes(b"\x89PNG\r\n\x1a\n")
            text = complete(VALID.replace("clutch/thing.py\n\n## Goal", "image.png\n\n## Goal"))
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
