"""Carried reproducer for a barrier blocking a disjoint ticket."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Carried bug regression script printing regression_result pass or defect for whether fill_slots lets a disjoint ticket pass a starvation barrier
# relates: [clutch/drain.py, clutch/tickets.py]
# owner: engine
# verified: 62301251
# hash: 1fe3f3dee6610a03ba7eb3075271006bf745d2ff35e5f47f22278dee37f2a613

import json
import sys
import traceback
from pathlib import Path


def main() -> int:
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        from clutch.drain import SKIP_LIMIT, fill_slots
        from clutch.tickets import Frontmatter, Ticket

        def ticket(stem, fence):
            return Ticket(
                stem=stem,
                frontmatter=Frontmatter(state="confirmed", source="human", priority="P1", kind="bug"),
                sections={},
                depends=(),
                context=(),
                on_demand=(),
                scope_fence=(fence,),
                verification=(),
                expected_minutes=20,
                stuck_minutes=40,
                runs_before=(),
            )

        busy, blocked, later = ticket("busy", "src"), ticket("blocked", "src/file"), ticket("later", "docs")
        selected, _ = fill_slots([blocked, later], [busy], 1, [], {"blocked": SKIP_LIMIT}, set())
        outcome, code = ("pass", 0) if selected == [later] else ("defect", 1)
    except Exception:
        traceback.print_exc(file=sys.stderr)
        outcome, code = "error", 2
    print(json.dumps({"regression_result": outcome}))
    return code


if __name__ == "__main__":
    sys.exit(main())
