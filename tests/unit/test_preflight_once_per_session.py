# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Unit tests that provider preflight runs once per engine session, reruns after routing or provider config changes or a failed or raising preflight, and is shared by concurrent pipeline preparation and _preflighted_llm
# relates: [clutch/__main__.py, clutch/providers.py, clutch/runner.py]
# owner: engine
# verified: ad681456
# hash: 8dc2b3452f1cc0014767fba4e6c60b83a1d8e105aa631e6eff1bb4efd96f61a3
import asyncio
from pathlib import Path
from types import SimpleNamespace as NS

import pytest

from clutch import runner
from clutch.providers import ADAPTERS, ProviderSession


class Exec:
    def __init__(self):
        self.calls = []
        self.fail = False
        self.raise_version = False

    async def run(self, argv, **kwargs):
        self.calls.append(argv)
        await asyncio.sleep(0)
        if self.raise_version:
            self.raise_version = False
            raise RuntimeError("version failed")
        if argv[0] == "probe" and self.fail:
            raise RuntimeError("probe failed")
        return 0, "1.0.0", ""


class Adapter:
    binary = "codex"

    def __init__(self, provider, *, exec_, **kwargs):
        self.provider, self.exec = provider, exec_
        self.cli_version = None

    async def invoke(self, request, model):
        await self.exec.run(["probe", model])


def config(model="one", package="codex-pkg"):
    provider = NS(name="codex", package=package, auth=None, limits=NS(concurrency=1), models_by_tier=NS(low="default"))
    return NS(providers=(provider,), routing=(NS(tier="low", candidates=(NS(provider="codex", model=model),)),), circuit_breaker=NS(), release=NS(pypi_token=""), state_dir=Path("/state"))


@pytest.fixture
def rig(monkeypatch):
    cfg = config()
    journal = NS(read=lambda: [])
    session = ProviderSession(cfg, journal=journal, clock=None, sleep=None, timers=NS())
    exec_ = Exec()
    events = []
    monkeypatch.setitem(ADAPTERS, "codex", Adapter)
    monkeypatch.setattr(runner, "engine_log", lambda *args: NS(event=lambda name, **fields: events.append((name, fields))))
    monkeypatch.setattr(runner, "call_timeout", lambda config: 1)
    monkeypatch.setattr(runner, "bind", lambda checkout, llm: (checkout.config, llm))
    checkout = NS(config=cfg, exec_=exec_, fs=None, env={}, repo=Path("/repo"), control=NS(providers=session), clock=None)
    return checkout, exec_, events


def calls(exec_):
    return [call[:2] for call in exec_.calls]


@pytest.mark.asyncio
async def test_equal_and_changed_snapshots(rig):
    checkout, exec_, events = rig
    first = await runner.prepare_pipeline(checkout)
    checkout.config = config()
    second = await runner.prepare_pipeline(checkout)
    assert first[1] is not second[1]
    assert first[1]._adapters["codex"].cli_version == second[1]._adapters["codex"].cli_version == "1.0.0"
    assert calls(exec_) == [["codex", "--version"], ["pnpm", "view"], ["probe", "one"]]
    assert events == [("phase_start", {"phase": "preflight"}), ("phase_end", {"phase": "preflight", "outcome": "ok"})]
    checkout.config = config(model="two")
    await runner.prepare_pipeline(checkout)
    assert calls(exec_)[3:] == [["codex", "--version"], ["pnpm", "view"], ["probe", "two"]]
    checkout.config = config(model="two", package="new-pkg")
    await runner.prepare_pipeline(checkout)
    assert exec_.calls[7] == ["pnpm", "view", "new-pkg", "version"]


@pytest.mark.asyncio
async def test_failed_and_raising_preflight_retry(rig):
    checkout, exec_, events = rig
    exec_.fail = True
    with pytest.raises(runner.Refusal, match="probe failed"):
        await runner.prepare_pipeline(checkout)
    exec_.fail = False
    exec_.raise_version = True
    with pytest.raises(RuntimeError, match="version failed"):
        await runner.prepare_pipeline(checkout)
    await runner.prepare_pipeline(checkout)
    assert calls(exec_) == [["codex", "--version"], ["pnpm", "view"], ["probe", "one"], ["codex", "--version"], ["codex", "--version"], ["pnpm", "view"], ["probe", "one"]]
    assert [fields["outcome"] for name, fields in events if name == "phase_end"] == ["failed", "failed", "ok"]


@pytest.mark.asyncio
async def test_concurrent_preparation_shares_probe(rig):
    checkout, exec_, events = rig
    await asyncio.gather(runner.prepare_pipeline(checkout), runner.prepare_pipeline(checkout))
    assert calls(exec_) == [["codex", "--version"], ["pnpm", "view"], ["probe", "one"]]
    assert len(events) == 2


@pytest.mark.asyncio
async def test_preflighted_llm_shares_session(rig, monkeypatch):
    from clutch import __main__

    checkout, exec_, _ = rig
    checkout.control.providers.timers = NS(reconstruct=lambda: None, fire_due=lambda: None)
    monkeypatch.setattr(__main__.runner, "call_timeout", lambda config: 1)
    await runner.prepare_pipeline(checkout)
    llm = await __main__._preflighted_llm(checkout, checkout.control.providers)
    assert llm._adapters["codex"].cli_version == "1.0.0"
    assert calls(exec_) == [["codex", "--version"], ["pnpm", "view"], ["probe", "one"]]
