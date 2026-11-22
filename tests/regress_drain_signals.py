"""Carried reproducer for signals that terminate a drain without a kill."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Standalone reproducer that checks a stop signal during a drain logs a killed `engine_stop` record.
# relates: [clutch/__main__.py, clutch/llm.py, clutch/runner.py, tests/integration/test_cli.py, tests/integration/test_drain.py]
# owner: engine
# verified: 7ad3c1c2
# hash: 58e6e1e15add61f4d429c08351d833fa4f7084ff4e0f77a2c98e49cd06d7021f

import asyncio
import contextlib
import io
import json
import sys
import tempfile
import traceback
from pathlib import Path


def main():
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        from clutch import __main__ as cli
        from clutch import runner
        from clutch.llm import FakeLLM
        from tests.cli_helpers import ENV
        from tests.drain_helpers import Clock, commit_ticket, confirmed, make_root
        from tests.integration.test_stages import agent

        temporary = tempfile.TemporaryDirectory()
        root = make_root(Path(temporary.name))
        commit_ticket(root, "work", confirmed())
    except Exception:
        traceback.print_exc(file=sys.stderr)
        print(json.dumps({"regression_result": "error"}))
        return 2

    callbacks = []
    name = "_engine_signals" if hasattr(cli, "_engine_signals") else "_serve" + "_signals"
    setattr(cli, name, lambda cb: (callbacks.append(cb), lambda: None)[1])

    class Blocking(FakeLLM):
        async def call(self, req):
            if callbacks:
                callbacks[0]()
                await asyncio.Event().wait()
            return await super().call(req)

    with contextlib.redirect_stdout(io.StringIO()):
        cli.main(["engine", "drain"], cwd=root, env=ENV, clock=Clock(), pipeline=lambda c: runner.bind(c, Blocking([agent({}, outcome="already_satisfied")])))
    events = [json.loads(line) for line in (root / ".clutch/state/engine.log").read_text().splitlines()]
    passed = bool(callbacks) and any(e["event"] == "engine_stop" and e["verb"] == "drain" and e["outcome"] == "killed" for e in events)
    temporary.cleanup()
    print(json.dumps({"regression_result": "pass" if passed else "defect"}))
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
