# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Tests diagnosis with a single model and with a majority-verdict panel, covering verdict choice, cost totals, the panel_facts journal signal, dropped members and the fallback when no verdict passes the schema
# relates: [clutch/artifacts.py, clutch/driver.py, clutch/panel.py, clutch/stages.py, tests/fakes.py, tests/unit/test_route_kinds_filter.py]
# owner: engine
# verified: 90b9b520
# hash: 7abda78cb6867656dd42857743c9c906ad5d534fb0f35618878738f4f38f6d6b
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from clutch import stages
from clutch.artifacts import Cost, Diagnosis, DiagnosisReply, Finding, StageResult
from clutch.driver import PanelResult, ProviderDroughtResult
from clutch.panel import DroppedMember
from tests.fakes import FakeFileSystem, FakeJournal
from tests.git_fake import GitFake
from tests.unit.test_route_kinds_filter import config


def cfg(size=None):
    panel = f", panel: {{size: {size}, combine: majority-verdict}}" if size else ""
    return config("  - {tier: medium, surface: diagnose, candidates: [{provider: codex, model: a}, {provider: claude, model: b}]" + panel + "}\n")


def member(verdict="retry", lesson="first", cost=Cost(tokens=10, seconds=2, attempts=1, usd=0.5, provider="codex", model="a")):
    return StageResult("ok", DiagnosisReply(verdict=verdict, lessons=[lesson]), [], cost)


class Driver:
    def __init__(self, single=None, panel=None):
        self.single = single or member()
        self.panel = panel
        self.calls = []
        self.events = []
        self.journal = FakeJournal()
        self.log = SimpleNamespace(event=lambda name, **kw: self.events.append((name, kw)))

    async def run(self, stage, material, **kwargs):
        self.calls.append(("run", kwargs))
        return self.single

    async def run_panel(self, stage, material, **kwargs):
        self.calls.append(("panel", kwargs))
        return self.panel


@pytest.fixture
def setup(tmp_path, monkeypatch):
    monkeypatch.setattr(stages, "_spec", lambda *args: SimpleNamespace(meta=SimpleNamespace(version="1.0")))
    monkeypatch.setattr(stages, "diagnose_stage", lambda *args: None)
    monkeypatch.setattr(stages, "lift_outbox", AsyncMock())
    ticket = SimpleNamespace(stem="item", frontmatter=SimpleNamespace(kind="bug", agent_tier="medium", agent_effort="low"), expected_minutes=1)
    material = stages.DiagnosisMaterial("ticket", "failed", "check", None, None)

    def build(driver, size=None):
        return SimpleNamespace(driver=driver, config=cfg(size), repo=tmp_path, worktree=lambda _: tmp_path, git=GitFake(rev_parse="sha"), fs=FakeFileSystem())

    return ticket, material, build


@pytest.mark.asyncio
@pytest.mark.parametrize("size", [None, 1])
async def test_single(setup, size):
    ticket, material, build = setup
    driver = Driver()
    ctx = build(driver, size)
    result = await stages.diagnose(ctx, ticket, material, attempt=1)
    expected = Diagnosis(
        produced_by_spec_version=1,
        produced_at_sha="sha",
        stem="item",
        attempt=1,
        terminal="failed",
        stage="check",
        verdict="retry",
        lessons=["first"],
        mechanical=None,
        trimmed_lessons=[],
        spec_version="1.0",
        provider="codex",
        model="a",
    )
    assert result == expected
    assert ctx.fs.files[ctx.repo / "tickets/item/diagnosis.json"] == (expected.model_dump_json(indent=2) + "\n").encode()
    assert driver.calls == [("run", dict(ticket="item", kind="bug", attempt=1, tier="medium", effort="low", stuck_budget=600.0, expected_budget=60.0, scope_fence=(), workspace=ctx.repo))]
    assert driver.events == []
    assert driver.journal.events == []
    driver = Driver(single=StageResult("timeout", None, [], Cost(seconds=4)))
    result = await stages.diagnose(build(driver, size), ticket, material, attempt=1)
    assert (result.verdict, result.mechanical, result.provider) == ("abandon-human", "no schema-valid verdict (timeout)", None)
    assert not driver.events
    assert driver.journal.events == []


@pytest.mark.asyncio
async def test_majority_and_facts(setup, monkeypatch):
    ticket, material, build = setup
    original = stages.write_diagnosis
    capture = AsyncMock(side_effect=original)
    monkeypatch.setattr(stages, "write_diagnosis", capture)
    second = member("escalate", "needs a stronger model", Cost(tokens=20, seconds=3, attempts=2, usd=0.25, provider="claude", model="b"))
    driver = Driver(panel=PanelResult([member(lesson="fix the import"), second], []))
    result = await stages.diagnose(build(driver, 2), ticket, material, attempt=1)
    assert (result.verdict, result.lessons, result.provider, result.model) == ("escalate", ["needs a stronger model"], "claude", "b")
    assert capture.await_args.kwargs["cost"] == Cost(tokens=30, seconds=5, attempts=3, usd=0.75, provider="claude", model="b")
    (event,) = driver.journal.events
    assert (event.type, event.ticket, event.key) == ("signal", "item", None)
    assert event.body == dict(
        signal="panel_facts",
        attempt=1,
        surface="diagnose",
        combiner="majority-verdict",
        member_count=2,
        members=[dict(provider="codex", model="a", verdict="retry"), dict(provider="claude", model="b", verdict="escalate")],
        verdict_counts={"retry": 1, "escalate": 1},
        dropped=[],
        merged=[],
        kept_index=None,
        agreement_kind="models",
    )
    assert driver.events == []
    single = Driver()
    await stages.diagnose(build(single), ticket, material, attempt=1)
    assert driver.calls[0][1] == dict(single.calls[0][1], size=2)
    for members, expected in [
        ([member(lesson="first"), member(lesson="second"), second], ("retry", ["first"])),
        ([member(), member("split", "split"), member("abandon-human", "human")], ("abandon-human", ["human"])),
    ]:
        d = Driver(panel=PanelResult(members, []))
        r = await stages.diagnose(build(d, 3), ticket, material, attempt=1)
        assert (r.verdict, r.lessons) == expected
    trimmed = member("escalate", "x" * 350)
    d = Driver(panel=PanelResult([member(), trimmed], []))
    r = await stages.diagnose(build(d, 2), ticket, material, attempt=1)
    assert r.trimmed_lessons == [0]
    d = Driver(panel=PanelResult([member(), member("escalate", cost=Cost())], []))
    await stages.diagnose(build(d, 2), ticket, material, attempt=1)
    assert capture.await_args.kwargs["cost"].tokens is None


@pytest.mark.asyncio
async def test_failures_and_drops(setup, monkeypatch):
    ticket, material, build = setup
    capture = AsyncMock(side_effect=stages.write_diagnosis)
    monkeypatch.setattr(stages, "write_diagnosis", capture)
    dropped = [DroppedMember(index=0, failure_class="infra_error")]
    quota = Finding(code="quota_exhausted", message="quota", paved_road="wait")
    d = Driver(panel=PanelResult([member("split", "survivor", Cost())], dropped, [quota]))
    r = await stages.diagnose(build(d, 2), ticket, material, attempt=1)
    assert (r.verdict, r.lessons, r.provider, r.model) == ("split", ["survivor"], "claude", "b")
    facts = d.journal.events[0].body
    assert (facts["dropped"], facts["member_count"], facts["verdict_counts"], facts["members"][0]["provider"]) == ([{"index": 0, "failure_class": "infra_error"}], 2, {"split": 1}, "claude")
    records = []
    for findings in ([quota], []):
        d = Driver(panel=PanelResult([], dropped + [DroppedMember(index=1, failure_class="infra_error")], findings))
        records.append(await stages.diagnose(build(d, 2), ticket, material, attempt=1))
        assert capture.await_args.kwargs["cost"] == Cost() and not d.events
        assert d.journal.events == []
    d = Driver(single=StageResult("infra_error", None, [quota], Cost()))
    records.append(await stages.diagnose(build(d), ticket, material, attempt=1))
    assert records[0] == records[1] == records[2]
    assert (records[0].verdict, records[0].lessons, records[0].mechanical) == ("abandon-human", [], "no schema-valid verdict (infra_error)")
    d = Driver(panel=PanelResult([member()], dropped, [quota]))
    r = await stages.diagnose(build(d, 2), ticket, material, attempt=1)
    assert r.verdict == "retry"
    for bad in (StageResult("timeout", None, [], Cost(seconds=4)), ProviderDroughtResult("infra_error", None, [], Cost(seconds=5), {"providers": ["codex"]})):
        d = Driver(panel=PanelResult([member(), bad], []))
        r = await stages.diagnose(build(d, 2), ticket, material, attempt=1)
        assert (r.verdict, r.lessons, r.mechanical) == ("abandon-human", [], f"no schema-valid verdict ({bad.outcome})")
        assert capture.await_args.kwargs["cost"] == bad.cost and not d.events
        assert d.journal.events == []
    d = Driver()
    ctx = build(d)
    ctx.config.routing = []
    await stages.diagnose(ctx, ticket, material, attempt=1)
    assert [call[0] for call in d.calls] == ["run"]
