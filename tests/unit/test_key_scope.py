# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test key scope
# relates: [clutch/artifacts.py, clutch/daemon.py, clutch/driver.py, clutch/enginelog.py, clutch/journal.py, clutch/llm.py, clutch/llmeffect.py]
# owner: engine
# verified: 9c24a9bd
# hash: 9ccc8ea7108d98d732fde59b44f29455093e332361936e8080c5916adba3bc61
import asyncio
import json
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from pydantic import BaseModel

from clutch import daemon, rework, stages
from clutch.artifacts import Cost, StageResult
from clutch.driver import Driver, LlmStage, Spool
from clutch.enginelog import EngineLog
from clutch.journal import Journal, run_seq
from clutch.llm import FakeLLM
from clutch.llmeffect import llm_key, scoped_seq
from clutch.redact import Redactor
from clutch.seams import LocalFileSystem


def test_scoped_sequence_and_keys():
    assert type(scoped_seq(None, 3)) is int
    assert scoped_seq(None, 3) == 3
    assert scoped_seq("sup", 3) == "sup-3"
    for bad in ("a/b", "", "7"):
        with pytest.raises(ValueError):
            scoped_seq(bad, 3)
    plain = llm_key("s", 2, "rework", 1, 1)
    assert llm_key("s", scoped_seq(None, 2), "rework", 1, 1) == plain
    assert len({plain, llm_key("s", scoped_seq("sup", 2), "rework", 1, 1), llm_key("s", scoped_seq("other", 2), "rework", 1, 1)}) == 3


class Echo(BaseModel):
    text: str


def test_driver_scoped_effect_and_integer_sequence(tmp_path):
    def clock():
        return datetime(2026, 1, 1, tzinfo=UTC)

    redactor = Redactor({})
    journal = Journal(tmp_path, clock)
    llm = FakeLLM(['{"text":"scoped"}', '{"text":"plain"}'])

    async def sleep(_):
        await asyncio.Event().wait()

    driver = Driver(
        llm=llm,
        journal=journal,
        redactor=redactor,
        spool=Spool(tmp_path, redactor, LocalFileSystem()),
        log=EngineLog(tmp_path / "log", redactor, clock),
        clock=clock,
        sleep=sleep,
        severity={},
        retry_cap=0,
    )
    stage = LlmStage(surface="rework", emits=Echo, gates=[], render=lambda *_: "echo")

    async def run():
        for scope in ("sup", None):
            result = await driver.run(stage, None, ticket="item", attempt=2, workspace=tmp_path, tier="low", effort="low", stuck_budget=60, expected_budget=30, scope_fence=(), key_scope=scope)
            assert result.artifact.text == ("scoped" if scope else "plain")

    asyncio.run(run())
    completions = [e.key for e in journal.read() if e.type == "effect_completion"]
    assert completions == ["llm/item/sup-0/rework/2/1", "llm/item/0/rework/2/1"]
    stage_events = [json.loads(line) for line in (tmp_path / "log").read_text().splitlines() if json.loads(line)["event"] in ("stage_start", "stage_end")]
    assert len(stage_events) == 4
    assert all(type(event["run_seq"]) is int and event["run_seq"] == 0 for event in stage_events)
    assert type(run_seq(journal.read(), "item")) is int and run_seq(journal.read(), "item") == 0


def test_lift_keys(tmp_path, monkeypatch):
    keys = []

    async def effect(action, *, key, ticket):
        keys.append(key)
        return {"commit": "sha"}

    ctx = SimpleNamespace(worktree=lambda _: tmp_path, driver=SimpleNamespace(effects=SimpleNamespace(run=effect)))
    monkeypatch.setattr(stages, "_lift_files", lambda *args: [tmp_path / "out"])
    monkeypatch.setattr(stages, "_validate_reports", lambda _: None)

    async def run():
        await stages.lift_outbox(ctx, "item", "checks", attempt=4, key_scope="sup")
        await stages.lift_outbox(ctx, "item", "checks", attempt=4)

    asyncio.run(run())
    assert keys == ["ticket-plane/item/sup-4/checks", "ticket-plane/item/4/checks"]


def test_apply_rework_scoped_publication(tmp_path, monkeypatch):
    ticket = SimpleNamespace(stem="item", stuck_minutes=1)
    order = rework.ReworkOrder(action="update", tickets=[{"stem": "item", "ticket": "new"}], stem="item", attempt=0, produced_by_spec_version=1, produced_at_sha="abc")
    result = StageResult(outcome="ok", artifact=order, cost=Cost(), findings=[])
    keys, scopes, cache = [], [], {}

    async def effect(action, *, key, ticket):
        keys.append(key)
        if key not in cache:
            cache[key] = await action()
        return cache[key]

    async def fake_rework(*args, **kwargs):
        scopes.append(kwargs["key_scope"])
        return result

    async def commit_edit(*args, edit, **kwargs):
        await edit()
        return "sha"

    git = SimpleNamespace(_run=AsyncMock(side_effect=["old", "new", "old", "new", "old"]), rev_parse=AsyncMock(return_value="abc"), commit_edit=AsyncMock(side_effect=commit_edit))
    ctx = SimpleNamespace(
        repo=tmp_path,
        worktree=lambda _: tmp_path,
        git=git,
        fs=SimpleNamespace(write=lambda *args: None),
        driver=SimpleNamespace(journal=SimpleNamespace(read=lambda: []), effects=SimpleNamespace(run=effect), redactor=Redactor({})),
    )
    monkeypatch.setattr(daemon, "parse_ticket", lambda *args: ticket)
    monkeypatch.setattr(daemon.runner, "capability", lambda *args: ("low", "low"))
    monkeypatch.setattr(daemon, "rework", fake_rework)
    monkeypatch.setattr(daemon, "record_supersedes", AsyncMock(return_value=[]))

    async def run():
        for scope in ("sup", None, None):
            assert (await daemon.apply_rework(ctx, ticket, [], attempt=0, key_scope=scope)).outcome == "ok"

    asyncio.run(run())
    assert keys == ["ticket-plane/item/sup-0/rework", "ticket-plane/item/0/rework", "ticket-plane/item/0/rework"]
    assert scopes == ["sup", None, None]
    assert git.commit_edit.await_count == 2


def test_rework_scopes_review_and_tree(tmp_path, monkeypatch):
    (tmp_path / "rework.md").write_text("unused")
    front = SimpleNamespace(source="x", state="confirmed", agent_tier="low", agent_effort="low")
    ticket = SimpleNamespace(stem="item", frontmatter=front, expected_minutes=1)
    reply = rework.ReworkReply(action="update", tickets=[{"stem": "item", "ticket": "new"}])
    seen, trees, keys = [], [], []
    history = [SimpleNamespace(ticket="item", key="llm/item/4/requisition_review/4/7")]
    journal = SimpleNamespace(read=lambda: history, append=lambda *args, **kwargs: None)

    async def fake_review(*args, **kwargs):
        seen.append((kwargs["key_scope"], kwargs["call_seq"]))
        keys.append(llm_key("item", scoped_seq(kwargs["key_scope"], kwargs["run_seq"]), "requisition_review", kwargs["attempt"], kwargs["call_seq"]))
        return SimpleNamespace(calls=1, verdict="snag", findings=[])

    async def fake_run(stage, *args, **kwargs):
        keys.append(llm_key("item", scoped_seq(kwargs["key_scope"], 4), "rework", 4, 1))
        await stage.review(reply, 1)
        return StageResult(outcome="ok", artifact=reply, cost=Cost(), findings=[])

    async def add(repo, tree, head):
        trees.append(tree)

    git = SimpleNamespace(rev_parse=AsyncMock(return_value="abc"), worktree_add_detached=add)
    ctx = SimpleNamespace(
        repo=tmp_path,
        specs_dir=tmp_path,
        config=SimpleNamespace(state_dir=tmp_path, review=SimpleNamespace(coverage_map=None)),
        git=git,
        fs=SimpleNamespace(write=lambda *args: None),
        driver=SimpleNamespace(journal=journal, run=fake_run),
    )
    monkeypatch.setattr(rework, "load_spec", lambda _: SimpleNamespace(meta=SimpleNamespace(version="1.0")))
    monkeypatch.setattr(rework, "validate_ticket", lambda *args: SimpleNamespace(frontmatter=front))
    monkeypatch.setattr(rework, "review_with_identity", fake_review)

    async def run():
        for scope in ("sup", None):
            await rework.rework(ctx, ticket, "old", [], attempt=4, workspace=tmp_path, tier="low", effort="low", stuck_budget=60, key_scope=scope)

    asyncio.run(run())
    assert seen == [("sup", 1), (None, 8)]
    assert trees == [tmp_path / "rework/item/sup-4/1", tmp_path / "rework/item/4/1"]
    assert keys == ["llm/item/sup-4/rework/4/1", "llm/item/sup-4/requisition_review/4/1", "llm/item/4/rework/4/1", "llm/item/4/requisition_review/4/8"]


def test_requisition_passes_scoped_sequence(tmp_path, monkeypatch):
    from clutch import requisition

    (tmp_path / "requisition_review.md").write_text("unused")
    spec = SimpleNamespace(meta=SimpleNamespace(version="1.0", effort="low"))
    ticket = SimpleNamespace(scope_fence=(), depends=(), stem="item")
    monkeypatch.setattr(requisition, "load_spec", lambda _: spec)
    monkeypatch.setattr(requisition, "review_target", lambda *args: ticket)
    monkeypatch.setattr(requisition, "_base_render", lambda *args: "base")
    monkeypatch.setattr(requisition, "render", lambda *args: "prompt")
    monkeypatch.setattr(requisition, "sibling_tickets_block", lambda *args: "none")
    calls = []

    async def llm_call(*args, **kwargs):
        calls.append((kwargs["run_seq"], kwargs["attempt"]))
        return dict(text='{"verdict":"approve","summary":"ok","findings":[]}', input_tokens=1, output_tokens=1, provider="fake", model="fake", usd=0.0)

    async def race(action, _):
        return await action()

    monkeypatch.setattr(requisition, "llm_call", llm_call)
    driver = SimpleNamespace(
        journal=SimpleNamespace(read=lambda: []),
        panel_members=lambda tier, surface: (),
        retry_cap=0,
        spool=SimpleNamespace(write=lambda *args: None),
        _active=True,
        race=race,
        effects=None,
        watched_llm=lambda: None,
        redactor=Redactor({}),
    )

    async def run():
        for scope in ("sup", None):
            result = await requisition.review_ticket(
                driver,
                repo=tmp_path,
                stem="item",
                text="ticket",
                specs_dir=tmp_path,
                coverage_map=None,
                tier="low",
                stem_slot="item",
                run_seq=4,
                attempt=4,
                call_seq=1,
                expected_budget=30,
                prior="none",
                key_scope=scope,
            )
            assert result.verdict == "approve"

    asyncio.run(run())
    assert calls == [("sup-4", 4), (4, 4)]
