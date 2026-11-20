import asyncio
from pathlib import Path
from types import SimpleNamespace

import pytest
from pydantic import BaseModel

from clutch.driver import Driver, LlmStage, ProviderDroughtResult, Spool
from clutch.llm import HANG, FakeLLM
from clutch.panel import DroppedMember
from clutch.providers import ProviderCallError, ProviderDrought
from clutch.redact import Redactor
from tests.fakes import FakeClock, FakeFileSystem, FakeJournal, turn


class Reply(BaseModel):
    text: str


class Log:
    def __init__(self):
        self.events = []

    def event(self, name, **fields):
        self.events.append((name, fields))


async def sleep(_):
    await asyncio.Event().wait()


def rig(script):
    clock, fs, redactor = FakeClock(), FakeFileSystem(), Redactor({})
    llm = FakeLLM(script)
    driver = Driver(llm=llm, journal=FakeJournal(clock), redactor=redactor, spool=Spool(Path("/spool"), redactor, fs), log=Log(), clock=clock, sleep=sleep, severity={}, retry_cap=0)
    stage = LlmStage("review", Reply, [], lambda *_: "prompt")
    args = dict(ticket="item", attempt=1, workspace=Path("/repo"), tier="medium", effort="low", stuck_budget=100, expected_budget=30, scope_fence=())
    return driver, stage, args, fs, clock, llm


@pytest.mark.asyncio
async def test_member_keys_spools_and_single_member():
    d, stage, args, fs, _, llm = rig(['{"text":"one"}', '{"text":"two"}'])
    result = await d.run_panel(stage, None, size=2, **args)
    assert [x.artifact.text for x in result.members] == ["one", "two"]
    assert [e.key for e in d.journal.read() if e.type == "effect_completion"] == ["llm/item/m0-0/review/1/1", "llm/item/m1-0/review/1/1"]
    assert {p for p in fs.files if p.name == "prompt.md"} == {Path("/spool/item/1/review/m0/call-01/prompt.md"), Path("/spool/item/1/review/m1/call-01/prompt.md")}
    assert len(llm.requests) == 2
    panel, stage, args, _, _, panel_llm = rig(['{"text":"one"}'])
    single, _, _, _, _, single_llm = rig(['{"text":"one"}'])
    await panel.run_panel(stage, None, size=1, **args)
    await single.run(stage, None, **args)
    assert [e.key for e in panel.journal.read() if e.type == "effect_completion"] == [e.key for e in single.journal.read() if e.type == "effect_completion"] == ["llm/item/0/review/1/1"]
    assert len(panel_llm.requests) == len(single_llm.requests) == 1


def failure():
    return ProviderCallError("fake", "failed", rc=1, stderr_tail="bad")


@pytest.mark.asyncio
@pytest.mark.parametrize("all_fail", [False, True])
async def test_dropped(all_fail):
    d, stage, args, _, _, _ = rig([failure(), failure() if all_fail else '{"text":"survivor"}'])
    result = await d.run_panel(stage, None, size=2, **args)
    assert result.dropped == [DroppedMember(index=i, failure_class="infra_error") for i in range(2 if all_fail else 1)]
    assert [m.artifact.text for m in result.members] == ([] if all_fail else ["survivor"])


@pytest.mark.asyncio
@pytest.mark.parametrize("elapsed", [30, 100])
async def test_budget(elapsed):
    d, stage, args, _, clock, llm = rig([])

    def first(_):
        clock.advance(elapsed)
        return '{"text":"one"}'

    llm.script = [first, '{"text":"two"}']
    deadlines = []
    race = d.race

    async def record(action, remaining):
        deadlines.append(remaining)
        return await race(action, remaining)

    d.race = record
    await d.run_panel(stage, None, size=2, **args)
    assert deadlines == ([100, 70] if elapsed == 30 else [100])
    assert [fields["stuck_budget"] for name, fields in d.log.events if name == "stage_start"] == ([100, 70] if elapsed == 30 else [100])
    assert len(llm.requests) == (2 if elapsed == 30 else 1)


@pytest.mark.asyncio
async def test_drought_stops():
    refusal = SimpleNamespace(providers=["fake"], waited_seconds=2, open_until=None, paved_road="wait")
    d, stage, args, _, _, llm = rig([ProviderDrought("medium", "review", refusal), '{"text":"unexpected"}'])
    result = await d.run_panel(stage, None, size=2, **args)
    assert len(result.members) == 1 and isinstance(result.members[0], ProviderDroughtResult)
    assert result.members[0].provider_drought == {"tier": "medium", "surface": "review", "providers": ["fake"]}
    assert result.dropped == [] and len(llm.requests) == 1


@pytest.mark.asyncio
async def test_abort_stops():
    d, stage, args, _, _, llm = rig([HANG, '{"text":"unexpected"}'])
    task = asyncio.create_task(d.run_panel(stage, None, size=2, **args))
    while not llm.requests:
        await turn()
    await d.abort_current()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert len(llm.requests) == 1 and d._active is None
