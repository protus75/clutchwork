"""Carried reproducer for phase rows sharing a kind in Recent Steps."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Carried reproducer for phase rows sharing a kind in Recent Steps.
# relates: [clutch/observe.py]
# owner: clutch/observe.py
# verified: d7719818
# hash: 96fa227405fe8cb85fec132e3282982bfe49e6f5c59e86be8db78e8a32df71e6

import json
import sys
import traceback
from pathlib import Path


def main() -> int:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    try:
        from clutch.observe import recent_steps

        events = [
            {"ts": "2026-01-01T00:00:00+00:00", "event": "phase_end", "phase": "preflight", "outcome": "ok"},
            {"ts": "2026-01-01T00:00:01+00:00", "event": "phase_end", "phase": "retro_check", "outcome": "ok"},
        ]
        rows = recent_steps(None, events, 2)
        defect = rows[0]["kind"] == rows[1]["kind"]
    except Exception:
        traceback.print_exc(file=sys.stderr)
        print(json.dumps({"regression_result": "error"}))
        return 2
    print(json.dumps({"regression_result": "defect" if defect else "pass"}))
    return 1 if defect else 0


if __name__ == "__main__":
    sys.exit(main())
