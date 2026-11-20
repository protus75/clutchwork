# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test route kinds filter
# relates: [clutch/config.py, clutch/driver.py, clutch/enginelog.py, clutch/journal.py, clutch/llm.py, clutch/providers.py, clutch/redact.py, clutch/seams.py]
# owner: engine
# verified: 9a610809
# hash: 2675a945e9838ef1c17a820d6a4a84f46536da135836d1517a53506ae71aa604
from pathlib import Path
from types import SimpleNamespace

import pytest

from clutch.config import ConfigError, load_config_text
from clutch.providers import ProviderSetupError, candidates, resolve, routed_conduct_paths


def config(rows):
    text = (
        """schema_version: 1
state_dir: .clutch/state
providers:
  - name: codex
    kind: cli
    package: pkg
    models_by_tier: {low: x, medium: x, high: x, max: x}
    limits: {concurrency: 1}
  - name: claude
    kind: cli
    package: pkg
    models_by_tier: {low: y, medium: y, high: y, max: y}
    limits: {concurrency: 1}
routing:
"""
        + rows
        + "\nreview: {}\nmerge: {}\nengine_plane_safety_inventory: [config.yaml]\n"
    )
    return load_config_text(text, path=Path("/repo/config.yaml"), cwd=Path("/repo"))


def test_kind_validation():
    row = "  - {tier: medium, surface: implement, KINDS candidates: [{provider: codex}]}\n"
    assert config(row.replace("KINDS", "kinds: [bug],")).routing[0].kinds == ["bug"]
    assert config(row.replace("KINDS", "")).routing[0].kinds is None
    for value in ("[]", "[epic]"):
        with pytest.raises(ConfigError):
            config(row.replace("KINDS", f"kinds: {value},"))


def test_selection_and_fallback():
    rows = """  - {tier: medium, surface: implement, kinds: [bug], candidates: [{provider: codex, model: a}, {provider: claude, model: extra}]}
  - {tier: medium, surface: implement, candidates: [{provider: codex, model: b}]}
  - {tier: medium, surface: review, kinds: [bug], candidates: [{provider: codex, model: c}]}
  - {tier: medium, surface: review, candidates: [{provider: codex, model: d}]}
"""
    cfg = config(rows)
    assert [resolve(cfg, "medium", "implement", k).model for k in ("bug", "feature", None)] == ["a", "b", "b"]
    assert [resolve(cfg, "medium", "diagnose", k).model for k in ("bug", "feature")] == ["c", "d"]
    assert [x.model for x in candidates(cfg, "medium", "implement", "bug")] == ["a", "extra"]
    assert [x.model for x in candidates(cfg, "medium", "implement", "feature")] == ["b"]
    cfg.routing = [cfg.routing[0], cfg.routing[3]]
    assert resolve(cfg, "medium", "implement", "feature").model == "d"
    cfg.routing.pop()
    with pytest.raises(ProviderSetupError):
        resolve(cfg, "medium", "implement", "feature")


def test_conduct_paths():
    cfg = config("""  - {tier: medium, surface: implement, kinds: [bug], candidates: [{provider: claude}]}
  - {tier: medium, surface: review, candidates: [{provider: codex}]}
""")
    assert set(routed_conduct_paths(cfg, Path("/repo"))) == {Path("/repo/CLAUDE.md"), Path("/repo/AGENTS.md")}


def test_driver_and_provider_propagate_kind(tmp_path):
    import asyncio
    from datetime import UTC, datetime
    from unittest.mock import AsyncMock

    from pydantic import BaseModel

    from clutch.driver import Driver, LlmStage, Spool
    from clutch.enginelog import EngineLog
    from clutch.journal import Journal
    from clutch.llm import FakeLLM, LLMRequest
    from clutch.providers import ProviderLLM
    from clutch.redact import Redactor
    from clutch.seams import LocalFileSystem

    class Reply(BaseModel):
        text: str

    clock = lambda: datetime(2026, 1, 1, tzinfo=UTC)  # noqa: E731

    async def sleep(_):
        await asyncio.Event().wait()

    redactor = Redactor({})
    llm = FakeLLM(['{"text":"one"}', '{"text":"two"}'])
    driver = Driver(
        llm=llm,
        journal=Journal(tmp_path, clock),
        redactor=redactor,
        spool=Spool(tmp_path / "spool", redactor, LocalFileSystem()),
        log=EngineLog(tmp_path / "log", redactor, clock),
        clock=clock,
        sleep=sleep,
        severity={},
        retry_cap=0,
    )
    stage = LlmStage(surface="implement", emits=Reply, gates=[], render=lambda *_: "prompt")

    async def run():
        for attempt, kind in enumerate(("bug", None), 1):
            await driver.run(stage, None, ticket="item", attempt=attempt, workspace=tmp_path, tier="medium", effort="low", stuck_budget=60, expected_budget=30, scope_fence=(), kind=kind)

    asyncio.run(run())
    assert [req.kind for req in llm.requests] == ["bug", None]
    cfg = config("""  - {tier: medium, surface: implement, kinds: [bug], candidates: [{provider: claude, model: a}]}
  - {tier: medium, surface: implement, candidates: [{provider: codex, model: b}]}
""")
    provider = object.__new__(ProviderLLM)
    provider._config = cfg
    provider._adapters = {name: SimpleNamespace(invoke=AsyncMock()) for name in ("claude", "codex")}

    async def calls():
        for kind in ("bug", None):
            await provider.call(LLMRequest(surface="implement", rendered="x", tier="medium", effort="low", ticket="item", worktree=None, kind=kind))

    asyncio.run(calls())
    assert provider._adapters["claude"].invoke.await_args.args[1] == "a"
    assert provider._adapters["codex"].invoke.await_args.args[1] == "b"


def test_ticket_stages_pass_kind(tmp_path, monkeypatch):
    import asyncio
    from types import SimpleNamespace
    from unittest.mock import AsyncMock

    from clutch import stages

    class Captured(Exception):
        pass

    calls = []

    async def capture(*args, **kwargs):
        calls.append(kwargs["kind"])
        raise Captured

    ticket = SimpleNamespace(stem="hero", frontmatter=SimpleNamespace(kind="bug", agent_tier="medium", agent_effort="low"), expected_minutes=10, stuck_minutes=20, scope_fence=())
    git = SimpleNamespace(rev_parse=AsyncMock(return_value="sha"), diff=AsyncMock(return_value="diff"))
    ctx = SimpleNamespace(driver=SimpleNamespace(run=capture), worktree=lambda _: tmp_path, repo=tmp_path, git=git)
    (tmp_path / "tickets/hero").mkdir(parents=True)
    (tmp_path / "tickets/hero/ticket.md").write_text("ticket")
    monkeypatch.setattr(stages, "_spec", lambda *args: None)
    monkeypatch.setattr(stages, "diagnose_stage", lambda *args: None)
    monkeypatch.setattr(stages, "prepare_worktree", AsyncMock(return_value=tmp_path))
    monkeypatch.setattr(stages, "implement_stage", lambda *args: (None, None))
    monkeypatch.setattr(stages, "review_stage", lambda *args: (None, None))

    async def run():
        for coro in (stages.diagnose(ctx, ticket, None, attempt=1), stages.implement(ctx, ticket, attempt=1), stages.review(ctx, ticket, None, attempt=1)):
            with pytest.raises(Captured):
                await coro

    asyncio.run(run())
    assert calls == ["bug", "bug", "bug"]
