"""Carried reproducer for the incomplete Implement reply."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Carried reproducer for the incomplete Implement reply.
# relates: [clutch/stages.py]
# owner: clutch/stages.py
# verified: d7719818
# hash: 667fae2b9cb9d76801dbd22a4d5d095ea4c502aae4c5eb2b994dc43256e1429f

import json
import sys


def main() -> int:
    try:
        from clutch.stages import ImplementReply
    except ImportError:
        print(json.dumps({"regression_result": "error"}))
        return 2

    from pydantic import ValidationError

    reply = {"outcome": "incomplete", "summary": "stopped", "surprises": "none", "dead_ends": "none", "predicted_vs_actual": "none", "findings": []}
    try:
        ImplementReply.model_validate(reply)
    except ValidationError:
        outcome, code = "defect", 1
    else:
        reply["findings"] = [{"code": "premise", "path": "ticket.md", "message": "contradiction", "paved_road": "correct ticket"}]
        try:
            ImplementReply.model_validate(reply)
        except ValidationError:
            outcome, code = "pass", 0
        else:
            outcome, code = "defect", 1
    print(json.dumps({"regression_result": outcome}))
    return code


if __name__ == "__main__":
    sys.exit(main())
