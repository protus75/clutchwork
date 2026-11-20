# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test stages host lock
# relates: [clutch/gates.py, clutch/stages.py]
# owner: engine
# verified: 9a610809
# hash: d9a445c1da0b1673319f88a0be0d9a84a8eb566f0cb55ed6cb7b4bc9dd1b418f
import asyncio
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import Mock

from clutch import stages
from clutch.gates import GateReport


def test_host_commands_are_serialized(monkeypatch, tmp_path):
    async def exercise():
        monkeypatch.setattr(stages, "HOST_COMMAND_LOCK", asyncio.Semaphore(1))
        monkeypatch.setattr(stages, "child_env", lambda env, config: dict(env))
        in_flight = 0
        maximum = 0

        async def run(argv, **kwargs):
            nonlocal in_flight, maximum
            in_flight += 1
            maximum = max(maximum, in_flight)
            await asyncio.sleep(0)
            in_flight -= 1
            return 0, "output", "error"

        driver = SimpleNamespace(clock=lambda: datetime(2020, 1, 1, tzinfo=timezone.utc), spool=Mock(), redactor=SimpleNamespace(scrub=lambda text: text))
        ctx = SimpleNamespace(driver=driver, env={}, config=None, exec_=SimpleNamespace(run=run), worktree=lambda stem: tmp_path)
        ticket = SimpleNamespace(stem="work", stuck_minutes=3)
        results = await asyncio.gather(*(stages.run_host_command(ctx, ticket, 2, ["command"], "check", "log") for _ in range(2)))
        assert maximum == 1
        assert results == [(stages.CommandResult(argv=["command"], rc=0, tail="outputerror", base_red=False, seconds=0.0), GateReport(code="check", verdict="pass", findings=[]))] * 2

    asyncio.run(exercise())
