# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Verify requisition review panel behavior.
# relates: [clutch/artifacts.py, clutch/driver.py, clutch/llm.py, clutch/llmeffect.py, clutch/panel.py, clutch/providers.py, clutch/requisition.py]
# owner: engine
# verified: 5110a5cc
# hash: 2e2abc6a72897b11c40f376f3883b5a124b3a86097755b9853745270244dc8ec
import asyncio
import json
from types import SimpleNamespace

import pytest

from clutch import requisition
from clutch.artifacts import Finding
from clutch.driver import Driver, _StuckBudget
from clutch.llm import LLMRequest
from clutch.llmeffect import llm_key, member_index
from clutch.panel import PanelMember, findings_union
from clutch.providers import ProviderCallError, ProviderDrought
from clutch.requisition import RequisitionReply, RequisitionVerdict
from tests.unit.test_route_kinds_filter import config


class MemoryPath:
    def __truediv__(self, name):
        return self

    def glob(self, pattern):
        return []

    def read_text(self):
        return "spec"


def finding(message="fence misses a.py"):
    return Finding(code="requisition_review", path="a.py", line=3, message=message, paved_road="fence it", kind="authoring_error")


def answer(verdict="approve", summary="fine", findings=(), **kwargs):
    return json.dumps(dict(verdict=verdict, summary=summary, findings=[f.model_dump() for f in findings], **kwargs))


def served(provider, model):
    return SimpleNamespace(provider=SimpleNamespace(name=provider), model=model)


SELECTED = (served("claude", "a"), served("codex", "b"))


@pytest.fixture
def run(monkeypatch):
    monkeypatch.setattr(requisition, "review_target", lambda *args: SimpleNamespace(scope_fence=()))
    monkeypatch.setattr(requisition, "_base_render", lambda *args: "base")
    monkeypatch.setattr(requisition, "load_spec", lambda _: SimpleNamespace(meta=SimpleNamespace(version="1.0", effort="high")))
    monkeypatch.setattr(requisition, "render", lambda *args: "prompt")
    repo = MemoryPath()

    def execute(script, selected=SELECTED, retry=1, scope=None):
        calls, watches, spools, events = [], [], [], []
        effects, llm, redactor = object(), object(), object()

        async def call(*args, **kwargs):
            calls.append(dict(args=args, **kwargs))
            value = script.pop(0)
            if isinstance(value, BaseException):
                raise value
            text, provider, model = value if isinstance(value, tuple) else (value, "claude", "a")
            return dict(text=text, input_tokens=1, output_tokens=2, provider=provider, model=model, usd=0.1)

        async def race(fn, timeout):
            if script and isinstance(script[0], _StuckBudget):
                raise script.pop(0)
            return await fn()

        monkeypatch.setattr(requisition, "llm_call", call)
        driver = SimpleNamespace(
            journal=SimpleNamespace(read=lambda: []),
            panel_members=lambda tier, surface: selected,
            retry_cap=retry,
            spool=SimpleNamespace(write=lambda *args: spools.append(args)),
            _active=None,
            begin_watch=lambda **kw: watches.append(kw),
            race=race,
            effects=effects,
            watched_llm=lambda: llm,
            redactor=redactor,
            log=SimpleNamespace(event=lambda event, **kw: events.append(dict(event=event, **kw))),
            _open_stage=None,
        )
        driver.stage = Driver.stage.__get__(driver)

        async def go():
            return await requisition.review_ticket(
                driver,
                repo=repo,
                stem="demo",
                text="ticket",
                specs_dir=repo,
                coverage_map=None,
                tier="high",
                stem_slot="demo",
                run_seq=2,
                attempt=2,
                call_seq=1,
                expected_budget="surface",
                prior="first",
                key_scope=scope,
            )

        return go, calls, watches, spools, events, (effects, llm, redactor), repo

    return execute


def expected_verdict(**fields):
    return RequisitionVerdict(
        produced_by_spec_version=1,
        produced_at_sha="6c967b608333d2eca9225f00eea2447bd8f2a755",
        stem="demo",
        ticket_sha="6c967b608333d2eca9225f00eea2447bd8f2a755",
        render_chars=4,
        spec_version="1.0",
        **fields,
    )


@pytest.mark.parametrize("selected", [(), SELECTED[:1]])
def test_single_unchanged(run, selected):
    go, calls, watches, spools, events, objects, repo = run(["bad", answer()], selected)
    verdict = asyncio.run(go())
    effects, llm, redactor = objects
    req = LLMRequest(surface="requisition_review", rendered="prompt", tier="high", effort="high", ticket=None, worktree=None)
    assert calls == [
        dict(args=(effects, llm, req, redactor), ticket="demo", stem="demo", run_seq=2, attempt=2, call_seq=1),
        dict(args=(effects, llm, req, redactor), ticket="demo", stem="demo", run_seq=2, attempt=2, call_seq=2),
    ]
    assert watches == [dict(owner="demo", ticket=None, run_sequence=2, surface="requisition_review", workspace=repo, expected_budget="surface", stuck_budget=600.0, scope_fence=(), attempt=2)] * 2
    assert spools == [
        ("demo/2", 2, "requisition_review/call-01/prompt.md", "prompt"),
        ("demo/2", 2, "requisition_review/call-01/output.txt", "bad"),
        ("demo/2", 2, "requisition_review/call-02/prompt.md", "prompt"),
        ("demo/2", 2, "requisition_review/call-02/output.txt", answer()),
    ]
    assert events == [
        dict(event="stage_start", stem="demo", attempt=2, surface="requisition_review", run_seq=2),
        dict(event="stage_end", stem="demo", attempt=2, surface="requisition_review", outcome="ok", run_seq=2, calls=2),
    ]
    assert verdict == expected_verdict(verdict="approve", summary="fine", findings=[], mechanical=None, provider="claude", model="a", calls=2)


def test_panel_worked_example(run):
    snag = answer("snag", "fence gap", [finding()])
    go, calls, watches, spools, events, _, repo = run(["bad", snag, (answer(), "codex", "b")])
    result = asyncio.run(go())
    keys = [llm_key(c["stem"], c["run_seq"], "requisition_review", c["attempt"], c["call_seq"]) for c in calls]
    assert keys == ["llm/demo/m0-2/requisition_review/2/1", "llm/demo/m0-2/requisition_review/2/2", "llm/demo/m1-2/requisition_review/2/1"]
    assert [member_index(k) for k in keys] == [0, 0, 1]
    assert [x[2] for x in spools] == [
        "requisition_review/m0/call-01/prompt.md",
        "requisition_review/m0/call-01/output.txt",
        "requisition_review/m0/call-02/prompt.md",
        "requisition_review/m0/call-02/output.txt",
        "requisition_review/m1/call-01/prompt.md",
        "requisition_review/m1/call-01/output.txt",
    ]
    assert watches == [dict(owner="demo", ticket=None, run_sequence=2, surface="requisition_review", workspace=repo, expected_budget="surface", stuck_budget=600.0, scope_fence=(), attempt=2)] * 3
    assert result == expected_verdict(verdict="snag", summary="fence gap\nfine", findings=[finding()], mechanical=None, provider="claude", model="a", calls=3)
    assert events == [
        dict(event="stage_start", stem="demo", attempt=2, surface="requisition_review", run_seq=2),
        dict(
            event="panel_facts",
            stem="demo",
            attempt=2,
            run_seq=2,
            surface="requisition_review",
            combiner="findings-union",
            member_count=2,
            verdict_counts={"snag": 1, "approve": 1},
            merged=[dict(finding=finding().model_dump(), agreement="1/2", members=[0])],
            members=[dict(provider="claude", model="a", verdict="snag"), dict(provider="codex", model="b", verdict="approve")],
            dropped=[],
            kept_index=None,
            agreement_kind="models",
        ),
        dict(event="stage_end", stem="demo", attempt=2, surface="requisition_review", outcome="gate_failed", run_seq=2, calls=3),
    ]


def test_scoped_and_unions(run):
    go, calls, _, _, events, _, _ = run([answer()], scope="sup")
    assert asyncio.run(go()).verdict == "approve" and calls[0]["run_seq"] == "sup-2" and len(calls) == 1
    assert all(e["event"] != "panel_facts" for e in events)
    go, _, _, _, _, _, _ = run([answer(), answer("rma", "bad", [finding()])])
    assert asyncio.run(go()) == expected_verdict(verdict="rma", summary="fine\nbad", findings=[finding()], mechanical=None, provider="claude", model="a", calls=2)
    go, _, _, _, events, _, _ = run([answer("snag", "a", [finding()]), answer("snag", "b", [finding("other")])])
    assert asyncio.run(go()).findings == [finding("fence misses a.py\nother")]
    assert events[1]["merged"][0]["agreement"] == "2/2" and events[1]["merged"][0]["members"] == [0, 1]
    replies = [RequisitionReply.model_validate_json(answer()), RequisitionReply.model_validate_json(answer("rma", "bad", [finding()]))]
    combined, _ = findings_union(replies, [PanelMember(provider="p", model="m", verdict=r.verdict) for r in replies], rma_code=None)
    assert isinstance(combined, RequisitionReply) and combined.findings == [finding()]


def test_failures(run):
    error = ProviderCallError("fake", "failed", rc=1, stderr_tail="bad")
    other = ProviderCallError("fake", "last", rc=2, stderr_tail="bad")
    go, _, _, _, events, _, _ = run([error, (answer("snag", "bad", [finding()]), None, None)])
    result = asyncio.run(go())
    assert (result.verdict, result.summary, result.findings) == ("snag", "bad", [finding()])
    assert events[1]["member_count"] == 2
    assert events[1]["merged"][0]["members"] == [0]
    assert events[1]["dropped"] == [dict(index=0, failure_class="infra_error")]
    assert events[1]["members"][0]["provider"] == "codex" and events[1]["merged"][0]["agreement"] == "1/1"
    go, _, _, _, events, _, _ = run([error, other])
    with pytest.raises(ProviderCallError) as exc:
        asyncio.run(go())
    assert exc.value is other and all(e["event"] != "panel_facts" for e in events)
    refusal = SimpleNamespace(providers=["fake"], waited_seconds=1, open_until=2, paved_road="retry")
    go, calls, _, _, _, _, _ = run([ProviderDrought("high", "requisition_review", refusal), answer()])
    with pytest.raises(ProviderDrought):
        asyncio.run(go())
    assert len(calls) == 1
    go, _, _, _, events, _, _ = run([answer(), _StuckBudget()])
    result = asyncio.run(go())
    assert result.mechanical == "timeout" and result.calls == 2 and all(e["event"] != "panel_facts" for e in events)
    go, calls, _, _, _, _, _ = run(["bad", "bad", answer()])
    assert asyncio.run(go()).mechanical == "invalid reply" and len(calls) == 2


def test_accessor():
    driver = Driver.__new__(Driver)
    driver._notify_config = None
    assert driver.panel_members("medium", "requisition_review") == ()
    rows = "  - {tier: medium, surface: requisition_review, candidates: [{provider: codex, model: a}, {provider: claude, model: b}], panel: {size: 2, combine: findings-union}}\n"
    driver._notify_config = (config(rows), {})
    assert [m.provider.name for m in driver.panel_members("medium", "requisition_review")] == ["codex", "claude"]
    driver._notify_config = (config(rows.replace("requisition_review", "review")), {})
    assert len(driver.panel_members("medium", "requisition_review")) == 1
    driver._notify_config = (config(rows.replace("requisition_review", "implement").replace(", panel: {size: 2, combine: findings-union}", "")), {})
    assert driver.panel_members("medium", "requisition_review") == ()


def test_real_dependent_reply_and_approve_union(run, monkeypatch):
    monkeypatch.setattr(requisition, "review_target", lambda *args: SimpleNamespace(scope_fence=("source.py",)))

    class MapPath:
        def read_text(self):
            return json.dumps({"files": {"source.py": ["tests/dependent.py"]}})

    monkeypatch.setattr(requisition, "dependent_errors", requisition.dependent_errors)
    # Inject the coverage map into the existing runner through a wrapper.
    original = requisition.review_ticket

    async def with_map(*args, **kwargs):
        kwargs["coverage_map"] = MapPath()
        return await original(*args, **kwargs)

    monkeypatch.setattr(requisition, "review_ticket", with_map)
    dep = [dict(path="tests/dependent.py", status="unaffected", reason="unchanged")]
    go, _, _, _, _, _, _ = run([answer(dependents=dep), answer(dependents=dep)])
    result = asyncio.run(go())
    assert result == expected_verdict(verdict="approve", summary="fine\nfine", findings=[], mechanical=None, provider="claude", model="a", calls=2)
    assert not hasattr(result, "dependents")


def test_each_member_has_own_retry_cap(run):
    go, calls, _, _, _, _, _ = run([answer(), "invalid", answer()])
    result = asyncio.run(go())
    assert result.verdict == "approve" and result.calls == 3
    assert [(c["run_seq"], c["call_seq"]) for c in calls] == [("m0-2", 1), ("m1-2", 1), ("m1-2", 2)]
