"""Host commands resolve the engine and do not inherit provider secrets."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Host commands resolve the engine and do not inherit provider secrets.
# relates: [clutch/stages.py]
# owner: clutch/stages.py
# verified: 9a610809
# hash: 536cf4b5f0bcb1fd8d9a3e0425ff834bf58ea21f9a49200640e6df503bcd7e9a

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from clutch import stages


@pytest.mark.parametrize("path", ["/usr/bin", None, ""])
def test_host_command_path_and_secrets(path, tmp_path):
    recorded = {}

    class Exec:
        async def run(self, argv, **kwargs):
            recorded.update(kwargs)
            return 0, "", ""

    env = {"FAKE_KEY": "x"}
    if path is not None:
        env["PATH"] = path
    ctx = SimpleNamespace(
        env=env,
        config=SimpleNamespace(providers=[SimpleNamespace(auth="FAKE_KEY")], release=SimpleNamespace(pypi_token="TOKEN")),
        exec_=Exec(),
        worktree=lambda stem: tmp_path,
        driver=SimpleNamespace(clock=lambda: datetime(2026, 1, 1), spool=SimpleNamespace(write=lambda *args: None), redactor=SimpleNamespace(scrub=lambda text: text)),
    )
    ticket = SimpleNamespace(stem="example", stuck_minutes=1)
    asyncio.run(stages.run_host_command(ctx, ticket, 1, ["host"], "host", "host.txt"))
    engine_bin = str(Path(sys.executable).parent)
    assert recorded["env"]["PATH"] == (engine_bin + os.pathsep + path if path else engine_bin)
    assert "FAKE_KEY" not in recorded["env"]
