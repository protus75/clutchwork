# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Tests the review stage with a single model and with a findings-union panel, covering verdict and finding merges, cost totals, the panel_facts journal signal, dropped members, non-ok results and effect keys
# relates: [clutch/artifacts.py, clutch/driver.py, clutch/llm.py, clutch/panel.py, clutch/providers.py, clutch/redact.py, clutch/seams.py, clutch/stages.py]
# owner: engine
# verified: 90b9b520
# hash: bb96d3be32ffc0726145d235ce87636e882c103adb6154dba8ffed0201fbc4c7
import asyncio
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from clutch import stages
from clutch.artifacts import Cost, Finding, ReviewVerdict, StageResult
from clutch.driver import Driver, LlmStage, PanelResult, ProviderDroughtResult, Spool
from clutch.llm import FakeLLM
from clutch.panel import DroppedMember
from clutch.providers import ProviderCallError, ProviderSetupError
from clutch.redact import Redactor
from clutch.seams import LocalFileSystem
from tests.fakes import FakeClock, FakeFileSystem, FakeJournal
from tests.git_fake import GitFake
from tests.unit.test_route_kinds_filter import config


def cfg(size=None):
    panel = f", panel: {{size: {size}, combine: findings-union}}" if size else ""
    return config("  - {tier: medium, surface: review, candidates: [{provider: codex, model: a}, {provider: claude, model: b}]" + panel + "}\n")


def finding(message="off by one", code="logic"):
    return Finding(code=code, path="a.py", line=3, message=message, paved_road="fix it")


def reply(verdict="snag", summary="bad loop", findings=None):
    return ReviewVerdict(verdict=verdict, summary=summary, findings=[finding()] if findings is None else findings)


def member(verdict=None, cost=Cost(tokens=10, seconds=2, attempts=1, usd=0.5, provider="codex", model="a")):
    return StageResult("ok", verdict or reply(), [], cost)


class Log:
    def __init__(self):
        self.events = []

    def event(self, name, **fields):
        self.events.append((name, fields))


class Recording:
    def __init__(self, single=None, panel=None):
        self.single = single or member()
        self.panel = panel
        self.calls = []
        self.log = Log()
        self.journal = FakeJournal()

    async def run(self, stage, invoice, **kwargs):
        self.calls.append(("run", kwargs))
        if isinstance(self.single, Exception):
            raise self.single
        return self.single

    async def run_panel(self, stage, invoice, **kwargs):
        self.calls.append(("panel", kwargs))
        return self.panel


@pytest.fixture
def setup(tmp_path, monkeypatch):
    (tmp_path / "tickets/item").mkdir(parents=True)
    (tmp_path / "tickets/item/ticket.md").write_text("ticket")
    monkeypatch.setattr(stages, "review_stage", lambda *args: (LlmStage("review", ReviewVerdict, [], lambda *_: "prompt"), SimpleNamespace(meta=SimpleNamespace(version="1.0"))))
    monkeypatch.setattr(stages, "lift_outbox", AsyncMock())
    ticket = SimpleNamespace(stem="item", frontmatter=SimpleNamespace(kind="bug", agent_tier="medium", agent_effort="low"), stuck_minutes=2, expected_minutes=1)

    def build(driver, size=None):
        return SimpleNamespace(
            driver=driver,
            config=cfg(size),
            repo=tmp_path,
            worktree=lambda _: tmp_path,
            git=GitFake(rev_parse="sha", diff="diff"),
            fs=FakeFileSystem(),
        )

    return ticket, build


def output(ctx):
    return ctx.fs.files[ctx.repo / "tickets/item/review.md"].decode()


@pytest.mark.asyncio
@pytest.mark.parametrize("size", [None, 1])
async def test_single(setup, size):
    ticket, build = setup
    driver = Recording()
    ctx = build(driver, size)
    result = await stages.review(ctx, ticket, None, attempt=1)
    artifact = stages.SnagList(
        produced_by_spec_version=1, produced_at_sha="sha", stem="item", reviewed_sha="sha", verdict="snag", summary="bad loop", findings=[finding()], spec_version="1.0", provider="codex", model="a"
    )
    assert result == StageResult("gate_failed", artifact, [finding()], Cost(tokens=10, seconds=2, attempts=1, usd=0.5, provider="codex", model="a"))
    assert [x[0] for x in driver.calls] == ["run"]
    assert driver.log.events == []
    assert driver.journal.events == []
    assert (
        output(ctx)
        == """# Review: snag

bad loop

## Findings

- [logic] a.py:3 off by one (do instead: fix it)

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "sha",
  "stem": "item",
  "reviewed_sha": "sha",
  "summary": "bad loop",
  "findings": [
    {
      "code": "logic",
      "path": "a.py",
      "line": 3,
      "message": "off by one",
      "paved_road": "fix it",
      "kind": null,
      "unit": null
    }
  ],
  "spec_version": "1.0",
  "provider": "codex",
  "model": "a",
  "verdict": "snag"
}
```
"""
    )


@pytest.mark.asyncio
async def test_shared_kwargs_and_combination(setup):
    ticket, build = setup
    single = Recording()
    await stages.review(build(single), ticket, None, attempt=1)
    second = member(reply("approve", "fine", []), Cost(tokens=20, seconds=3, attempts=2, usd=0.25, provider="claude", model="b"))
    driver = Recording(panel=PanelResult([member(), second], []))
    ctx = build(driver, 2)
    result = await stages.review(ctx, ticket, None, attempt=1)
    assert driver.calls[0][1] == dict(single.calls[0][1], size=2)
    assert result.outcome == "gate_failed"
    assert result.cost == Cost(tokens=30, seconds=5, attempts=3, usd=0.75, provider="codex", model="a")
    artifact = stages.read_review(output(ctx))
    assert (artifact.verdict, artifact.summary, artifact.findings, artifact.provider) == ("snag", "bad loop\nfine", [finding()], "codex")
    (event,) = driver.journal.events
    assert (event.type, event.ticket, event.key) == ("signal", "item", None)
    assert event.body["signal"] == "panel_facts" and event.body["surface"] == "review" and event.body["attempt"] == 1
    assert event.body["members"] == [dict(provider="codex", model="a", verdict="snag"), dict(provider="claude", model="b", verdict="approve")]
    assert event.body["agreement_kind"] == "models" and event.body["verdict_counts"] == {"snag": 1, "approve": 1}
    assert driver.log.events == []


@pytest.mark.asyncio
@pytest.mark.parametrize("verdict,expected", [("approve", "approve"), ("rma", "rma")])
async def test_worst_verdict(setup, verdict, expected):
    ticket, build = setup
    other = reply(verdict, "other", [] if verdict == "approve" else [finding(code="ticket")])
    driver = Recording(panel=PanelResult([member(reply("approve", "fine", [])), member(other)], []))
    ctx = build(driver, 2)
    result = await stages.review(ctx, ticket, None, attempt=1)
    assert result.artifact.verdict == expected
    assert result.outcome == ("ok" if expected == "approve" else "gate_failed")
    assert stages.read_review(output(ctx)) == result.artifact


@pytest.mark.asyncio
async def test_merged_and_unknown_tokens(setup):
    ticket, build = setup
    driver = Recording(panel=PanelResult([member(), member(reply(summary="again", findings=[finding("different")]), Cost())], []))
    ctx = build(driver, 2)
    result = await stages.review(ctx, ticket, None, attempt=1)
    assert result.cost.tokens is None
    assert result.artifact.findings == [finding("off by one\ndifferent")]
    merged = driver.journal.events[0].body["merged"]
    assert len(merged) == 1 and merged[0]["agreement"] == "2/2" and merged[0]["members"] == [0, 1]


@pytest.mark.asyncio
async def test_dropped_and_empty(setup):
    ticket, build = setup
    dropped = [DroppedMember(index=0, failure_class="infra_error")]
    driver = Recording(panel=PanelResult([member(cost=Cost())], dropped))
    ctx = build(driver, 2)
    result = await stages.review(ctx, ticket, None, attempt=1)
    facts = driver.journal.events[0].body
    assert result.outcome == "gate_failed" and result.artifact.summary == "bad loop"
    assert facts["dropped"] == [{"index": 0, "failure_class": "infra_error"}]
    assert facts["member_count"] == 2 and facts["members"][0]["provider"] == "claude"
    assert facts["merged"][0]["members"] == [0] and facts["merged"][0]["agreement"] == "1/1"
    driver = Recording(panel=PanelResult([], dropped))
    ctx = build(driver, 2)
    assert await stages.review(ctx, ticket, None, attempt=1) == StageResult("infra_error", None, [], Cost())
    assert not ctx.fs.files and not driver.log.events
    assert driver.journal.events == []


@pytest.mark.asyncio
@pytest.mark.parametrize("bad", [StageResult("timeout", None, [], Cost(seconds=4)), ProviderDroughtResult("infra_error", None, [], Cost(), {"providers": ["codex"]})])
async def test_non_ok(setup, bad):
    ticket, build = setup
    driver = Recording(panel=PanelResult([member(), bad], []))
    ctx = build(driver, 2)
    assert await stages.review(ctx, ticket, None, attempt=1) is bad
    assert not ctx.fs.files and not driver.log.events
    assert driver.journal.events == []


@pytest.mark.asyncio
async def test_route_error(setup):
    ticket, build = setup
    error = ProviderSetupError("missing")
    driver = Recording(single=error)
    ctx = build(driver)
    ctx.config.routing = []
    with pytest.raises(ProviderSetupError) as exc:
        await stages.review(ctx, ticket, None, attempt=1)
    assert exc.value is error and [x[0] for x in driver.calls] == ["run"]


@pytest.mark.asyncio
@pytest.mark.parametrize("size", [None, 1, 2])
async def test_effect_keys_and_provider_failures(setup, tmp_path, size):
    ticket, build = setup
    clock, redactor = FakeClock(), Redactor({})
    failure = ProviderCallError("fake", "failed", rc=1, stderr_tail="bad")
    answer = reply().model_dump_json()
    llm = FakeLLM([failure, answer] if size == 2 else [answer])

    async def sleep(_):
        await asyncio.Event().wait()

    driver = Driver(llm=llm, journal=FakeJournal(clock), redactor=redactor, spool=Spool(tmp_path, redactor, LocalFileSystem()), log=Log(), clock=clock, sleep=sleep, severity={}, retry_cap=0)
    ctx = build(driver, size)
    result = await stages.review(ctx, ticket, None, attempt=1)
    assert result.outcome == "gate_failed"
    keys = [e.key for e in driver.journal.read() if e.type == "effect_completion"]
    assert keys == (["llm/item/m1-0/review/1/1"] if size == 2 else ["llm/item/0/review/1/1"])
    if size == 2:
        facts = next(e.body for e in driver.journal.events if e.type == "signal" and e.body.get("signal") == "panel_facts")
        assert facts["dropped"] == [{"index": 0, "failure_class": "infra_error"}]


@pytest.mark.asyncio
async def test_all_provider_calls_fail(setup, tmp_path):
    ticket, build = setup
    clock, redactor = FakeClock(), Redactor({})
    failure = ProviderCallError("fake", "failed", rc=1, stderr_tail="bad")

    async def sleep(_):
        await asyncio.Event().wait()

    driver = Driver(
        llm=FakeLLM([failure, failure]),
        journal=FakeJournal(clock),
        redactor=redactor,
        spool=Spool(tmp_path, redactor, LocalFileSystem()),
        log=Log(),
        clock=clock,
        sleep=sleep,
        severity={},
        retry_cap=0,
    )
    ctx = build(driver, 2)
    assert await stages.review(ctx, ticket, None, attempt=1) == StageResult("infra_error", None, [], Cost())
    assert not ctx.fs.files and all(name != "panel_facts" for name, _ in driver.log.events)
    assert not any(e.type == "signal" and e.body.get("signal") == "panel_facts" for e in driver.journal.events)
