"""Carried reproducer for redundant drain retro checks."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Carried bug regression script that prints a regression_result showing whether drain runs the retro check again when the settled-terminal count has not changed
# relates: [clutch/drain.py, clutch/journal.py]
# owner: engine
# verified: 331196ce
# hash: 1c2a925a1e7bef607b38b28b706e2d428c94d3476b323da1d95a1cce9baed7e7

import asyncio
import json
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace


def main() -> int:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    try:
        from clutch import drain
        from clutch.journal import EventType

        config = SimpleNamespace(state_dir=Path("/state"), providers=[], release=SimpleNamespace(pypi_token=""), drain=SimpleNamespace(max_runtime_hours=1))
        events = [SimpleNamespace(type=EventType.STATE_TRANSITION, body={"to": "merged"})]
        checkout = SimpleNamespace(config=config, env={}, clock=lambda: datetime(2026, 1, 1, tzinfo=timezone.utc), sleep=None, control=None, journal=SimpleNamespace(read=lambda: events))
        drain.engine_log = lambda *args: SimpleNamespace(event=lambda *args, **kwargs: None)
        d = drain._Drain(checkout, None, frozenset())

        class Retro:
            due = False
            calls = 0

            async def __call__(self, *, forced):
                self.calls += 1

            async def abort_current(self):
                pass

        d.retro = Retro()

        async def run():
            await d._run_retro(forced=False)
            await d._run_retro(forced=False)

        asyncio.run(run())
        if d.retro.calls not in (1, 2):
            raise ValueError(f"unexpected call count: {d.retro.calls}")
        defect = d.retro.calls == 2
    except Exception:
        traceback.print_exc(file=sys.stderr)
        print(json.dumps({"regression_result": "error"}))
        return 2
    print(json.dumps({"regression_result": "defect" if defect else "pass"}))
    return 1 if defect else 0


if __name__ == "__main__":
    sys.exit(main())
