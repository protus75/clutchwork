"""Carried reproducer for uncontended paths in the hot paths list."""

import json
import sys
import traceback
from pathlib import Path


def main() -> int:
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        from clutch.observe import _hot_paths
        from clutch.tickets import Frontmatter, Ticket

        meta = Frontmatter(state="confirmed", source="human", priority="P1", kind="feature")
        tickets = [Ticket(stem, meta, {}, (), (), (), (path,), (), 1, 2) for stem, path in (("one", "one.py"), ("two", "two.py"))]
        rows = _hot_paths(tickets)
        defect = any(row["count"] == 1 for row in rows)
        if rows and not defect:
            raise ValueError("unexpected hot paths")
    except Exception:
        traceback.print_exc(file=sys.stderr)
        print(json.dumps({"regression_result": "error"}))
        return 2
    print(json.dumps({"regression_result": "defect" if defect else "pass"}))
    return 1 if defect else 0


if __name__ == "__main__":
    sys.exit(main())
