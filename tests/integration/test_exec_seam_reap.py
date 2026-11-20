# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test exec seam reap
# relates: [clutch/seams.py, tests/waiting.py]
# owner: engine
# verified: 148a8874
# hash: 6d1a1b23f3a169ccf9f2efc589f51f63b96700526bbb66a163fc59d1b7dbec6a
import asyncio
import json
import os
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from clutch.seams import SubprocessExec
from tests.waiting import group_exited, wait_until


async def run(code, **kwargs):
    return await SubprocessExec().run([sys.executable, "-c", code], cwd=os.getcwd(), env=os.environ, timeout=kwargs.pop("timeout", 10), **kwargs)


@pytest.mark.asyncio
async def test_concurrent_exit_codes(caplog):
    results = await asyncio.gather(*(run("raise SystemExit(3)") for _ in range(20)))
    assert [result[0] for result in results] == [3] * 20
    assert not any(record.name.startswith("asyncio") and ("exit status already read" in record.message or "Unknown child process" in record.message) for record in caplog.records)


@pytest.mark.asyncio
async def test_usage_and_independent_peak_memory():
    script = """
import asyncio
import json
import os
import sys
from clutch.seams import SubprocessExec

async def main():
    big, small = [], []
    exec_ = SubprocessExec()
    async def run(code, callback):
        await exec_.run([sys.executable, "-c", code], cwd=os.getcwd(), env=os.environ, timeout=10, on_rusage=callback)
    await asyncio.gather(
        run("import time; x=bytearray(200_000_000); t=time.process_time()+0.2\\nwhile time.process_time()<t: pass", big.append),
        run("pass", small.append),
    )
    print(json.dumps({"big": [item.model_dump() for item in big], "small": [item.model_dump() for item in small]}))

asyncio.run(main())
"""
    _, stdout, _ = await SubprocessExec().run([sys.executable, "-c", script], cwd=Path(__file__).resolve().parents[2], env=os.environ, timeout=10)
    usage = json.loads(stdout, object_hook=lambda value: SimpleNamespace(**value))
    big, small = usage.big, usage.small
    assert len(big) == len(small) == 1
    assert big[0].user_s + big[0].sys_s > 0
    assert small[0].max_rss_kb > 0
    assert big[0].max_rss_kb - small[0].max_rss_kb >= 100000


@pytest.mark.asyncio
async def test_timeout_reaps_and_reports_usage():
    groups, usage = [], []
    with pytest.raises(TimeoutError):
        await run("import time; time.sleep(60)", timeout=0.3, on_spawn=groups.append, on_rusage=usage.append)
    assert len(usage) == 1
    assert len(groups) == 1 and group_exited(groups[0])


@pytest.mark.asyncio
async def test_output_and_tail():
    lines = []
    result = await run('import sys; sys.stdout.write("first\\ntail"); sys.stderr.write("error"); sys.exit(3)', on_stdout_line=lines.append)
    assert result == (3, "first\ntail", "error")
    assert lines == ["first\n", "tail"]


@pytest.mark.asyncio
async def test_timeout_with_many_unbounded_children():
    groups = []
    exec_ = SubprocessExec()
    tasks = [asyncio.create_task(exec_.run([sys.executable, "-c", "import time; time.sleep(60)"], cwd=os.getcwd(), env=os.environ, timeout=None, on_spawn=groups.append)) for _ in range(33)]
    try:
        await wait_until(lambda: len(groups) == 33)
        usage, timed_group = [], []
        start = time.monotonic()
        with pytest.raises(TimeoutError):
            await run("import time; time.sleep(60)", timeout=0.3, on_spawn=timed_group.append, on_rusage=usage.append)
        assert time.monotonic() - start < 5
        assert len(usage) == 1
        assert len(timed_group) == 1 and group_exited(timed_group[0])
    finally:
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
