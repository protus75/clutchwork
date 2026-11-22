"""Carried regression for serve test waits under load."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Carried regression script that checks serve test waits stay deterministic under load: fake-clock until pacing, graceful FixtureLoop stop and a bounded stuck-wait refusal.
# relates: [clutch/seams.py, tests/fakes.py, tests/harness/host_loop.py, tests/integration/serve_rig.py]
# owner: engine
# verified: 543c80a2
# hash: 61de2222674ae16ae08a403f7ab7f03720a2be2c24830e4dd0159e1ece68c672

import asyncio
import json
import sys
import tempfile
import traceback
from pathlib import Path
from types import SimpleNamespace


async def check():
    from clutch.seams import LocalFileSystem
    from tests import fakes
    from tests.harness.host_loop import FixtureLoop, LoopRefused
    from tests.integration import serve_rig

    class FastTime:
        value = 0

        def monotonic(self):
            self.value += 100
            return self.value

    old_time = fakes.time
    fakes.time = FastTime()
    polls = 0

    def predicate():
        nonlocal polls
        polls += 1
        return polls == 300

    try:
        try:
            await serve_rig.until(SimpleNamespace(time=fakes.FakeClock()), predicate)
            until_ok = polls == 300
        except AssertionError:
            until_ok = False
    finally:
        fakes.time = old_time

    class RecordingExec:
        def __init__(self):
            self.killed = []

        def kill_group(self, pgid):
            self.killed.append(pgid)

    scratch = Path(__file__).resolve().parents[1] / ".clutch/scratch"
    scratch.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=scratch) as directory:
        root = Path(directory)
        active = root / ".clutch/state/control/active.json"
        active.parent.mkdir(parents=True)
        active.write_text(json.dumps({"lifecycle_id": "x", "hold_id": None}))
        clock = fakes.FakeClock()
        exec_ = RecordingExec()
        loop = FixtureLoop(root, "regression", exec_=exec_, fs=LocalFileSystem(), clock=clock, sleep=asyncio.sleep, notifications=None)

        async def serve():
            await asyncio.sleep(5.5)
            return (0, "", "")

        loop.task = asyncio.create_task(serve())
        await loop.stop()
        stop_ok = not loop.task.cancelled() and loop.task.result() == (0, "", "")

        steps = 0

        async def fake_sleep(seconds):
            nonlocal steps
            steps += 1
            if steps > 20:
                raise RuntimeError("fake-clock wait did not terminate")
            clock.advance(seconds)

        loop.task = None
        loop.timeout = 0.3
        loop.sleep = fake_sleep
        try:
            await loop.until(lambda: False)
        except LoopRefused:
            stuck_ok = 1 <= steps <= 20
        except Exception:
            stuck_ok = False
        else:
            stuck_ok = False
    return until_ok and stop_ok and stuck_ok


def main():
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        passed = asyncio.run(check())
    except Exception:
        traceback.print_exc(file=sys.stderr)
        print(json.dumps({"regression_result": "error"}))
        return 2
    print(json.dumps({"regression_result": "pass" if passed else "defect"}))
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
