"""Carried reproducer for Reject-queue reoffers."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Carried reproducer for Reject-queue reoffers.
# relates: [clutch/config.py, clutch/drain.py]
# owner: engine
# verified: d7719818
# hash: 205c97d234ccafbcdf076017324c0da4549111e8c6066aad51703328f58ab569

import json
import sys
import traceback
from pathlib import Path
from types import SimpleNamespace


def main():
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    try:
        import clutch.drain as drain

        awaiting_operator = drain.awaiting_operator
        reofferable = drain.reofferable
    except AttributeError:
        print(json.dumps({"regression_result": "defect"}))
        return 1
    except Exception:
        traceback.print_exc(file=sys.stderr)
        print(json.dumps({"regression_result": "error"}))
        return 2
    try:
        from clutch.config import Caps

        history = [SimpleNamespace(type="state_transition", ticket="work", body={"to": "gate_failed", "routed": "reject_queue"})]
        spent = history + [SimpleNamespace(type="cap_consumed", ticket="work", body={"cap": "retry"})]
        limits = Caps(retry=1)
        defect = not reofferable(history, "work", limits) or not awaiting_operator(spent, "work", limits)
    except Exception:
        traceback.print_exc(file=sys.stderr)
        print(json.dumps({"regression_result": "error"}))
        return 2
    print(json.dumps({"regression_result": "defect" if defect else "pass"}))
    return 1 if defect else 0


if __name__ == "__main__":
    sys.exit(main())
