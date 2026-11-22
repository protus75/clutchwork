"""Carried reproducer for serve's Reject-queue re-offer selection."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Carried reproducer checking serve's scheduler re-offers a Reject-queue ticket for dispatch
# relates: [clutch/scheduler.py, tests/integration/test_scheduler.py]
# owner: clutch/scheduler.py
# verified: 82d23237
# hash: 5c9cf43ea2b47375df6bf5dcab4b56098087e91131cac0a2791a8dbf971807a2

import asyncio
import inspect
import json
import sys
import tempfile
import traceback
from pathlib import Path


def main():
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    try:
        from clutch.scheduler import Scheduler

        if "caps" not in inspect.signature(Scheduler).parameters:
            result = "defect"
        else:
            from tests.loop_helpers import Rig

            with tempfile.TemporaryDirectory() as directory:
                rig = Rig(Path(directory))
                rig.add("work")
                rig.transition("work", "gate_failed", routed="reject_queue")
                ticket = asyncio.run(rig.scheduler.dispatch_next())
                result = "pass" if ticket is not None and ticket.stem == "work" else "defect"
    except Exception:
        traceback.print_exc(file=sys.stderr)
        result = "error"
    print(json.dumps({"regression_result": result}))
    return {"pass": 0, "defect": 1, "error": 2}[result]


if __name__ == "__main__":
    sys.exit(main())
