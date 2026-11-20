"""Reproduce acceptance of an Implement premise finding without a path."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Reproduce acceptance of an Implement premise finding without a path.
# relates: [clutch/stages.py]
# owner: clutch/stages.py
# verified: d7719818
# hash: 0f89d5b25a5c46a758da9aa5b11dbbfc075a0331c0e5d624f181617c9fa50539

import json

from pydantic import ValidationError

from clutch.stages import ImplementReply


def main() -> None:
    reply = {
        "outcome": "premise_failed",
        "summary": "unfinished",
        "surprises": "none",
        "dead_ends": "none",
        "predicted_vs_actual": "none",
        "findings": [{"code": "premise", "message": "unfinished", "paved_road": "finish"}],
    }
    try:
        ImplementReply.model_validate_json(json.dumps(reply))
    except ValidationError:
        passed = True
    else:
        passed = False
    print(json.dumps({"regression_result": "pass" if passed else "defect"}))
    raise SystemExit(0 if passed else 1)


if __name__ == "__main__":
    main()
