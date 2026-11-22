"""Carried reproducer for duplicate serve retro checks."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Standalone regression script that calls Serve.check_retro twice and prints a JSON pass/defect/error result based on whether the retro_check phase is logged once or twice for the same journal state
# relates: [clutch/journal.py, clutch/serve.py]
# owner: clutch/serve.py
# verified: 2182d51e
# hash: 8693c91c8c602b9fa41bd58f794301d7ee8f2e2ccb640a51450a201165c28398

import asyncio
import json
import sys
import traceback
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace


def main() -> int:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    try:
        from clutch import serve
        from clutch.journal import EventType

        @dataclass
        class Checkout:
            config: object
            journal: object
            clock: object

        s = object.__new__(serve.Serve)
        s.retro_checked = None
        s.retro_due = False
        log = []
        s.log = SimpleNamespace(event=lambda name, **fields: log.append(name))
        config = SimpleNamespace(retro=object())
        s.checkout = Checkout(config, SimpleNamespace(read=lambda: [SimpleNamespace(type=EventType.STATE_TRANSITION, body={"to": "merged"})]), lambda: "now")
        s.control = SimpleNamespace(load_config=lambda: config)
        serve.snapshot_config = lambda value: value
        serve.project_window = lambda value: value
        serve.suppressing_failure = lambda value: None
        serve.due_trigger = lambda *args, **kwargs: None

        async def check():
            await s.check_retro()
            await s.check_retro()

        asyncio.run(check())
        count = log.count("phase_start")
        if count not in (1, 2):
            raise ValueError(f"unexpected phase count: {count}")
        defect = count == 2
    except Exception:
        traceback.print_exc(file=sys.stderr)
        print(json.dumps({"regression_result": "error"}))
        return 2
    print(json.dumps({"regression_result": "defect" if defect else "pass"}))
    return 1 if defect else 0


if __name__ == "__main__":
    sys.exit(main())
