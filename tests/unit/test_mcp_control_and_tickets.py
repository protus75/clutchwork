"""Mutation tools exercise shared owners through fake process and provider seams."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Unit tests for the MCP server's mutation tools: ticket authoring, lint, ordering, verdicts, the suggestion box, triage, engine start and control, retro, and domain-error projection. They use fake process, lock, and provider seams.
# relates: [clutch/__main__.py, clutch/artifacts.py, clutch/box.py, clutch/control.py, clutch/hostfiles.py, clutch/journal.py, clutch/lockfile.py]
# owner: engine
# verified: 66bcb385
# hash: 108bf3891135d89df3a3c0a1251b8667a5af5379565e13da24ecd6df66b83445

import asyncio
import io
import json
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from clutch import __main__ as entry
from clutch import box, control, hostfiles, mcp, observe, retro, runner, serve, tickets, triage
from clutch.artifacts import Finding
from clutch.journal import EventType, Journal
from clutch.lockfile import CommitLockTimeout, LockHeld
from clutch.providers import ProviderSetupError
from clutch.seams import ExecutableNotFound, LocalFileSystem
from tests.config_helpers import VALID
from tests.fakes import FakeClock, FakeFileSystem
from tests.git_fake import GitFake


@pytest.fixture
def rig(tmp_path, monkeypatch):
    (tmp_path / "tickets").mkdir()
    (tmp_path / "config.yaml").write_text(VALID)
    clock = FakeClock()
    cfg = SimpleNamespace(state_dir=tmp_path / "state", drain=SimpleNamespace(max_ticket_minutes=90))
    checkout = runner.Checkout(tmp_path, cfg, {}, None, GitFake(describe="instance", git_common_dir=tmp_path / ".git"), Journal(cfg.state_dir, clock), LocalFileSystem(), clock)
    server = mcp.ClutchMCPServer(default_cwd=tmp_path, spawn=Mock(return_value=321))
    monkeypatch.setattr(server, "checkout", lambda repo: (checkout, None))
    return server, checkout


def call(server, tool, **arguments):
    return server.dispatch("tools/call", {"name": "clutch_" + tool, "arguments": arguments})


@asynccontextmanager
async def unlocked(*args, **kwargs):
    yield


def held(verb):
    @asynccontextmanager
    async def lock(*args, **kwargs):
        raise LockHeld(Path("lock"), {"verb": verb})
        yield

    return lock


def test_catalog_and_actor_schema(rig):
    server, _ = rig
    catalog = server.dispatch("tools/list", {})["tools"]
    # Wrong: expose UI verdicts to the model or hide ordinary tools.
    assert {t["name"]: t.get("_meta") for t in catalog} == {
        name: {"ui": {"visibility": ["app"]}}
        if name.startswith("clutch_app_")
        else {"ui": {"resourceUri": mcp.DASHBOARD_URI}, "com.google.antigravity/ui": {"entrypoints": [{"type": "aux_pane", "title": "ClutchWork"}, {"type": "global", "title": "ClutchWork"}]}}
        if name == "clutch_open_dashboard"
        else None
        for name in mcp.TOOLS
    }
    for name in ("ticket_confirm", "ticket_reject"):
        with pytest.raises(mcp.InvalidParams):
            call(server, name, stem="sample", extension=True)
    with pytest.raises(mcp.InvalidParams):
        call(server, "box_dismiss", ids=[])


def test_authoring_and_copies(rig, tmp_path):
    server, _ = rig
    result = call(server, "ticket_new", stem="sample")["structuredContent"]
    # Wrong: return a path without writing the draft, or omit structured findings.
    assert result["path"] == "tickets/sample/ticket.md"
    # Wrong: Author receipt names wrong stem.
    assert result["stem"] == "sample"
    # Wrong: Author receipt omits installed guide.
    assert result["guide"].endswith("/docs/host-authoring.md")
    # Wrong: New skeleton starts confirmed.
    assert "state: draft" in (tmp_path / result["path"]).read_text()
    # Wrong: Author receipt loses lint findings.
    assert {"code", "message", "paved_road"} <= result["findings"][0].keys()
    for arguments in ({"stem": "sample"}, {"stem": "Bad_Stem"}, {"stem": "broken", "kind": "bug"}):
        # Wrong: Existing tickets overwritten.
        assert call(server, "ticket_new", **arguments)["isError"]
    (tmp_path / "observed.txt").write_bytes(b"observed failure")
    call(server, "ticket_new", stem="bug-sample", kind="bug", evidence=["observed.txt"])
    # Wrong: Evidence/reference copies contain wrong bytes.
    assert (tmp_path / "tickets/bug-sample/evidence/observed.txt").read_bytes() == b"observed failure"
    (tmp_path / "ref.png").write_bytes(b"reference content")
    call(server, "ticket_new", stem="graphic", kind="graphics", reference=["ref.png"])
    # Wrong: Graphics copies use wrong source.
    assert (tmp_path / "tickets/graphic/reference/ref.png").read_bytes() == b"reference content"


@pytest.mark.parametrize("exit_code", [0, 1, 2])
def test_lint_projection(rig, monkeypatch, exit_code):
    server, checkout = rig
    finding = {"path": "tickets/sample/ticket.md", "code": "grammar", "message": "specific finding", "paved_road": "repair heading"}
    target = AsyncMock(return_value={"valid": 3, "total": 5, "exit_code": exit_code, "findings": [finding], "refusals": [{"message": "missing named ticket", "paved_road": "author it"}]})
    monkeypatch.setattr(tickets, "lint_tickets", target)
    result = call(server, "ticket_lint", stems=["named"])
    # Wrong: Named lint selection dropped.
    target.assert_awaited_once_with(checkout, ["named"])
    # Wrong: treat findings as refusal, or hide unreadable/missing selections as findings.
    assert result["structuredContent"] == (
        {"code": "lint_refused", "message": "missing named ticket", "paved_road": "author it"} if exit_code == 2 else {"valid": 3, "total": 5, "valid_all": exit_code == 0, "findings": [finding]}
    )


def test_lint_missing_and_order_owner(rig, monkeypatch, tmp_path):
    server, checkout = rig
    for stem in ("missing", "../escaped"):
        # Wrong: Named lint selection dropped.
        assert call(server, "ticket_lint", stems=[stem])["structuredContent"] == {
            "code": "lint_refused",
            "message": "no ticket file",
            "paved_road": "create tickets/<stem>/ticket.md with clutch ticket new <stem>",
        }
    path = tmp_path / "tickets/sample/ticket.md"
    path.parent.mkdir()
    path.write_text("---\npriority: P2\n---\n## Runs before\n- later\n\n## Goal / Why\nbody\n")
    target = Mock(side_effect=lambda stem, text, repo: SimpleNamespace(frontmatter=SimpleNamespace(priority="P0"), runs_before=()))
    # Exercise actual order and write; substitute only grammar validation of this tiny fixture.
    result = tickets.order_ticket(checkout, "sample", priority="P0", runs_before=[], validate_fn=target)
    # Wrong: Ordering receipt has old priority.
    assert result == {"stem": "sample", "path": "tickets/sample/ticket.md", "priority": "P0", "runs_before": []}
    # Wrong: Ordering cannot clear runs-before.
    assert path.read_text() == "---\npriority: P0\n---\n## Goal / Why\nbody\n"
    for state in ("merged", "running"):
        facts = SimpleNamespace(states={"sample": state}, orphans=set())
        with pytest.raises(runner.Refusal):
            tickets.order_ticket(checkout, "sample", priority="P0", admission_facts_fn=lambda _: facts, validate_fn=target)
    target = Mock(return_value={"ordered": "sample"})
    monkeypatch.setattr(tickets, "order_ticket", target)
    # Wrong: Ordering receipt ignored.
    assert call(server, "ticket_order", stem="sample", priority="P1", runs_before=["next"])["structuredContent"] == {"ordered": "sample"}
    # Wrong: MCP ordering drops priority.
    target.assert_called_once_with(checkout, "sample", priority="P1", runs_before=["next"])


@pytest.mark.parametrize("app", [False, True])
@pytest.mark.parametrize("kill", [False, True])
def test_verdict_routing(rig, monkeypatch, app, kill):
    server, checkout = rig
    target = AsyncMock(return_value={"actor": "distinct receipt"})
    monkeypatch.setattr(runner, "submit_verdict", target)
    name = ("app_" if app else "") + "ticket_" + ("reject" if kill else "confirm")
    args = {"reason": "observed defect"} if kill else {}
    # Wrong: Verdict owner receipt ignored.
    assert call(server, name, stem="sample", **args)["structuredContent"] == {"actor": "distinct receipt"}
    # Wrong: Reject routed as confirm.
    target.assert_awaited_once_with("sample", checkout, kill=kill, extension=app, reason="observed defect" if kill else None)


@pytest.mark.parametrize("extension", [False, True])
def test_verdict_submits_actor_and_reason(rig, monkeypatch, extension):
    server, checkout = rig
    monkeypatch.setattr(runner, "verdict", AsyncMock(side_effect=LockHeld(Path("lock"), {"verb": "serve"})))
    monkeypatch.setattr(runner, "ticket_pending", AsyncMock(return_value=False))
    published = []

    async def submit(c, exc, verb, **kwargs):
        return await runner.submit_engine(c, exc, verb, **kwargs, read_active_fn=lambda *a: ("life", "hold"), publish_fn=lambda state, request, fs: published.append(request))

    result = asyncio.run(runner.submit_verdict("sample", checkout, kill=True, extension=extension, reason="reason", submit_fn=submit))
    # Wrong: Queued verdict reported applied.
    assert result["submitted"] is True
    # Wrong: UI inbox verdict has operator actor.
    assert (published[0].actor, published[0].operator_reason) == ("extension" if extension else "operator", "reason")
    # Wrong: Verdict receipt loses request identity.
    assert result["request_id"] == published[0].request_id
    # Wrong: Reject routed as confirm.
    assert call(server, "ticket_reject", stem="sample", reason="  ")["structuredContent"]["code"] == "blank_reason"
    with pytest.raises(runner.Refusal, match="blank reason"):
        asyncio.run(submit(checkout, LockHeld(Path("lock"), {"verb": "drain"}), "reject", stem="sample", reason=""))


def test_verdict_output_and_repeat_refusal(rig, monkeypatch):
    _, checkout = rig

    async def fake_verdict(*args, **kwargs):
        print("confirmed sample")
        return 7

    monkeypatch.setattr(runner, "verdict", fake_verdict)
    result = asyncio.run(runner.submit_verdict("sample", checkout, kill=False))
    # Wrong: Verdict outcome discarded.
    assert (result["output"], result["outcome"], result["submitted"]) == ("confirmed sample\n", 7, False)
    monkeypatch.setattr(runner, "verdict", AsyncMock(side_effect=runner.Refusal("already kept at this ticket content", "edit ticket")))
    with pytest.raises(runner.Refusal, match="already kept"):
        asyncio.run(runner.submit_verdict("sample", checkout, kill=False))


def test_box_suggest_and_dismiss(rig, monkeypatch):
    server, checkout = rig
    result = call(server, "box_suggest", summary="specific useful idea")["structuredContent"]
    # Wrong: New suggestion reported duplicate.
    assert result["created"] is True
    message = box.Box(checkout.config.state_dir / box.BOX_DIR, checkout.fs).get(result["id"])
    # Wrong: Suggestion loses producer origin.
    assert (message.summary, message.origin) == ("specific useful idea", "session")
    # Wrong: Duplicate suggestion reported newly created.
    assert call(server, "box_suggest", summary="specific useful idea")["structuredContent"] == {"id": result["id"], "created": False}
    # Wrong: Blank suggestion accepted.
    assert call(server, "box_suggest", summary=" ")["structuredContent"]["code"] == "blank_summary"
    monkeypatch.setattr(runner, "_locked", unlocked)
    monkeypatch.setattr(runner, "reap", AsyncMock())
    dismiss = AsyncMock(return_value=["named suggestion dismissed"])
    monkeypatch.setattr(triage, "dismiss", dismiss)
    # Wrong: Dismiss owner not invoked.
    assert call(server, "box_dismiss", ids=[result["id"]])["structuredContent"] == {"lines": ["named suggestion dismissed"]}
    # Wrong: Dismiss named IDs dropped.
    dismiss.assert_awaited_once_with(checkout, [result["id"]])
    monkeypatch.setattr(runner, "_locked", held("serve"))
    # Wrong: Held dismiss lock has wrong error code.
    assert call(server, "box_dismiss", ids=[result["id"]])["structuredContent"]["code"] == "lock_held"


def test_box_triage_idle_and_busy(rig, monkeypatch):
    server, checkout = rig
    monkeypatch.setattr(runner, "_locked", unlocked)
    monkeypatch.setattr(runner, "reap", AsyncMock())
    session = SimpleNamespace(close=AsyncMock())
    monkeypatch.setattr(entry, "build_control", lambda c: SimpleNamespace(providers=session))
    monkeypatch.setattr(entry, "_preflighted_llm", AsyncMock(return_value="llm"))
    target = AsyncMock(return_value=[("box-named", "triaged named")])

    async def route(c, ids, **kwargs):
        return await original(c, ids, **kwargs, triage_pass_fn=target)

    original = runner.triage_or_submit
    monkeypatch.setattr(runner, "triage_or_submit", route)
    id_ = call(server, "box_suggest", summary="triage me")["structuredContent"]["id"]
    # Wrong: Triage result dropped.
    assert call(server, "box_triage", ids=[id_])["structuredContent"] == {"submitted": False, "lines": [["box-named", "triaged named"]]}
    # Wrong: Triage uses wrong provider.
    target.assert_awaited_once_with(checkout, "llm", frozenset([id_]))
    # Wrong: Triage provider session leaked.
    session.close.assert_awaited_once()
    # Wrong: Unknown triage IDs not checked.
    assert call(server, "box_triage", ids=["unknown"])["isError"]
    for verb in ("serve", "drain"):
        monkeypatch.setattr(runner, "_locked", held(verb))
        result = asyncio.run(
            original(
                checkout,
                [id_],
                lock_ctx_factory=runner._locked,
                build_control_fn=Mock(),
                preflighted_llm_fn=AsyncMock(),
                submit_fn=AsyncMock(return_value=SimpleNamespace(request_id="triage-request")),
            )
        )
        # Wrong: Triage inbox receipt drops request id.
        assert result == {"submitted": True, "request_id": "triage-request"}
    monkeypatch.setattr(runner, "_locked", held("release"))
    # Wrong: Non-engine holder accepts inbox mutation.
    assert call(server, "box_triage", ids=[id_])["structuredContent"]["code"] == "lock_held"


@pytest.mark.parametrize("mode", ["drain", "serve"])
def test_detached_engine_start(rig, monkeypatch, mode):
    server, checkout = rig
    monkeypatch.setattr(observe, "lock_holder", lambda state: None)
    monkeypatch.setattr(serve, "capture_startup_baseline", Mock(return_value=(17, "old-life")))
    wait = Mock(return_value=True)
    monkeypatch.setattr(serve, "wait_detached_startup", wait)
    result = call(server, "engine_start", mode=mode)
    output = checkout.config.state_dir / f"{mode}.out"
    # Wrong: Detached start loses spawned PID.
    assert result["structuredContent"] == {"pid": 321, "output": str(output)}
    # Wrong: Detached child argv changes mode.
    server.spawn.assert_called_once_with([sys.executable, "-m", "clutch", "engine", mode], cwd=checkout.repo, env=server.env, output=output)
    if mode == "serve":
        # Wrong: Serve startup confirmation loses baseline.
        wait.assert_called_once_with(checkout.config.state_dir, 321, output, prior_size=17, prior_lifecycle="old-life")
        wait.return_value = False
        # Wrong: Domain refusals reported as successful tools.
        assert call(server, "engine_start", mode=mode)["isError"]
        wait.side_effect = runner.Refusal("startup refused", "repair")
        # Wrong: Startup refusal text includes paved road twice.
        assert call(server, "engine_start", mode=mode)["structuredContent"]["message"] == "startup refused"
    monkeypatch.setattr(observe, "lock_holder", lambda state: "live")
    server.spawn.reset_mock()
    # Wrong: Start spawns while live writer holds lock.
    assert call(server, "engine_start", mode=mode)["structuredContent"]["code"] == "lock_held"
    # Wrong: Spawn attempted before held-lock refusal.
    server.spawn.assert_not_called()


@pytest.mark.parametrize("verb", [None, "release", "serve", "drain"])
def test_ping_projection(rig, monkeypatch, verb):
    server, checkout = rig
    state = checkout.config.state_dir
    state.mkdir()
    (state / "clutch.lock").write_text(json.dumps({"verb": verb, "pid": 83, "started_at": "timestamp"}))
    monkeypatch.setattr(observe, "lock_holder", lambda state: "live" if verb else None)
    (state / "control").mkdir()
    (state / "control/active.json").write_text(json.dumps({"lifecycle_id": "life", "hold_id": "hold"}))
    engine = verb in {"serve", "drain"}
    # Wrong: Ping hides live non-engine holder.
    assert call(server, "engine_control", action="ping")["structuredContent"] == {
        "alive": verb is not None,
        "engine": engine,
        "verb": verb,
        "pid": 83 if verb else None,
        "started_at": "timestamp" if verb else None,
        "lifecycle_id": "life" if engine else None,
        "hold_id": "hold" if engine else None,
    }


@pytest.mark.parametrize("action", ["pause", "resume", "stop", "kill"])
def test_control_idle_and_submission(rig, monkeypatch, action):
    server, checkout = rig
    lock = Mock()
    # Wrong: report stop/kill success with no engine, or refuse idle pause/resume.
    if action in {"stop", "kill"}:
        with pytest.raises(runner.Refusal, match="nothing running"):
            asyncio.run(runner.control_engine(checkout, action, lock_factory=lambda *a, **kw: lock))
    else:
        # Wrong: Idle pause/resume not projected.
        assert asyncio.run(runner.control_engine(checkout, action, lock_factory=lambda *a, **kw: lock)) == {"status": "nothing_running"}
    # Wrong: Writer lock not released.
    lock.release.assert_called_once()
    lock.acquire.side_effect = LockHeld(Path("lock"), {"verb": "serve"})
    requests = []

    async def submit(c, exc, verb):
        return await runner.submit_engine(c, exc, verb, read_active_fn=lambda *a: ("engine-life", "engine-hold"), publish_fn=lambda state, request, fs: requests.append(request))

    async def route(c, verb):
        return await original(c, verb, lock_factory=lambda *a, **kw: lock, submit_fn=submit)

    original = runner.control_engine
    monkeypatch.setattr(runner, "control_engine", route)
    result = call(server, "engine_control", action=action)["structuredContent"]
    # Wrong: Control request receipt loses submitted state.
    assert result == {"status": "submitted", "request_id": requests[0].request_id}
    # Wrong: Resume control request loses hold.
    assert (requests[0].verb, requests[0].lifecycle_id, requests[0].hold_id) == (action, "engine-life", "engine-hold" if action == "resume" else None)
    if action == "resume":
        with pytest.raises(runner.Refusal, match="no current hold"):
            asyncio.run(runner.submit_engine(checkout, LockHeld(Path("lock"), {"verb": "drain"}), action, read_active_fn=lambda *a: ("life", None)))


def test_retro_idle_and_busy(rig, monkeypatch):
    server, checkout = rig
    monkeypatch.setattr(runner, "_locked", unlocked)
    monkeypatch.setattr(runner, "reap", AsyncMock())
    session = SimpleNamespace(close=AsyncMock())
    monkeypatch.setattr(entry, "build_control", lambda c: SimpleNamespace(providers=session))
    monkeypatch.setattr(runner, "pipeline", lambda c: "pipeline")
    target = AsyncMock(return_value=None)
    monkeypatch.setattr(retro, "Retro", lambda c, dispatch: target)
    # Wrong: MCP retro outcome missing.
    assert call(server, "engine_retro")["structuredContent"] == {"outcome": 0}
    # Wrong: Manual retro obeys automatic due thresholds.
    target.assert_awaited_once_with(forced=True)
    # Wrong: Retro provider session leaked.
    session.close.assert_awaited_once()
    submit = AsyncMock(return_value=SimpleNamespace(request_id="retro-request"))
    # Wrong: Queued retro reported failed.
    assert asyncio.run(runner.run_or_submit_retro(checkout, Mock(), lock_ctx_factory=held("drain"), build_control_fn=Mock(), config_reloader_fn=Mock(), submit_fn=submit)) == 0
    # Wrong: Retro enqueues stop instead.
    assert submit.await_args.args[2] == "retro"


@pytest.mark.parametrize(
    "error",
    [
        LockHeld(Path("lock"), {"verb": "release"}),
        CommitLockTimeout(Path("commit.lock"), None),
        tickets.IntakeRefused(Finding(code="intake", message="intake failed", paved_road="repair")),
        ProviderSetupError("provider unavailable"),
        ExecutableNotFound("missing executable"),
        hostfiles.MarkerCorruption(),
    ],
)
def test_domain_errors(rig, monkeypatch, error):
    server, _ = rig
    monkeypatch.setattr(server, "call_tool", Mock(side_effect=error))
    result = call(server, "engine_retro")
    # Wrong: Domain refusals reported as successful tools.
    assert result["isError"] is True
    # Wrong: Domain errors lose message.
    assert all(result["structuredContent"][key] for key in ("code", "message", "paved_road"))


def test_stdio_domain_noise_and_extension_rejection(tmp_path, monkeypatch, capsys):
    def noisy(*args):
        print("domain chatter")
        return {"receipt": "specific"}, "specific"

    monkeypatch.setattr(mcp.ClutchMCPServer, "call_tool", noisy)
    requests = [
        {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "clutch_engine_retro"}},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "clutch_ticket_confirm", "arguments": {"stem": "sample", "extension": True}}},
    ]
    output = io.StringIO()
    mcp.serve_stdio(stdin=io.StringIO("\n".join(json.dumps(r) for r in requests)), stdout=output, default_cwd=tmp_path)
    replies = [json.loads(line) for line in output.getvalue().splitlines()]
    # Wrong: domain prints corrupt the transport or extension becomes model-settable.
    assert replies[0] == {"jsonrpc": "2.0", "id": 1, "result": {"content": [{"type": "text", "text": "specific"}], "structuredContent": {"receipt": "specific"}}}
    # Wrong: Extension silently accepted.
    assert replies[1]["error"]["code"] == -32602
    # Wrong: Domain noise leaks onto stdout.
    assert capsys.readouterr().err == "domain chatter\n"


@pytest.mark.parametrize("app", [False, True])
def test_same_content_repeat_verdict(rig, monkeypatch, app):
    server, checkout = rig
    path = checkout.repo / "tickets/sample/ticket.md"
    path.parent.mkdir()
    path.write_text("---\nstate: confirmed\n---\n")
    history = [
        SimpleNamespace(type=EventType.STATE_TRANSITION, ticket="sample", body={"to": "gate_failed", "routed": "reject_queue"}),
        SimpleNamespace(type=EventType.SIGNAL, ticket="sample", body={"signal": "reject_verdict", "verdict": "keep", "actor": "operator", "ticket_sha": "same-sha"}),
        SimpleNamespace(type=EventType.STATE_TRANSITION, ticket="sample", body={"to": "gate_failed", "routed": "reject_queue"}),
    ]
    checkout.journal.read = lambda: history
    monkeypatch.setattr(runner, "Lockfile", lambda *a, **kw: Mock())
    monkeypatch.setattr(runner, "reap", AsyncMock())
    monkeypatch.setattr(runner, "intake", AsyncMock(return_value=SimpleNamespace(refused={})))
    checkout.git._overrides["rev_parse"] = "same-sha"
    result = call(server, "app_ticket_confirm" if app else "ticket_confirm", stem="sample")
    # Wrong: allow identical operator keeps or apply that restriction to human UI clicks.
    if app:
        # Wrong: Operator/UI actors inverted.
        assert result["structuredContent"]["actor"] == "extension"
    else:
        # Wrong: Operator/UI actors inverted.
        assert result["isError"] and "already kept at this ticket content" in result["structuredContent"]["message"]


def test_omitted_reject_reason_and_triage_request(rig, monkeypatch):
    server, checkout = rig
    verdict = AsyncMock(return_value=8)
    monkeypatch.setattr(runner, "verdict", verdict)
    # Wrong: Verdict outcome discarded.
    assert call(server, "ticket_reject", stem="sample")["structuredContent"]["outcome"] == 8
    # Wrong: Reject routed as confirm.
    verdict.assert_awaited_once_with("sample", checkout, kill=True, extension=False)
    # Wrong: rely on the inbox to reject blank reasons while the unlocked path accepts them.
    assert call(server, "ticket_reject", stem="sample", reason=" ")["structuredContent"]["code"] == "blank_reason"
    request = asyncio.run(runner.submit_engine(checkout, LockHeld(Path("lock"), {"verb": "drain"}), "triage", ids=["named-box"], read_active_fn=lambda *a: ("life", None), publish_fn=lambda *a: None))
    # Wrong: Triage request loses IDs.
    assert (type(request), request.ids, request.actor, request.lifecycle_id) == (control.TriageRequest, ["named-box"], "operator", "life")


def test_invalid_order_and_unreadable_lint(rig, monkeypatch):
    server, checkout = rig
    path = checkout.repo / "tickets/sample/ticket.md"
    path.parent.mkdir()
    path.write_text("not a valid ticket")
    # Wrong: Domain refusals reported as successful tools.
    assert call(server, "ticket_order", stem="sample", priority="P1")["isError"]
    # Wrong: swallow an unreadable tickets directory as an empty successful lint.
    monkeypatch.setattr(Path, "iterdir", Mock(side_effect=PermissionError("unreadable tickets")))
    # Wrong: Lint findings confused with refusal.
    assert call(server, "ticket_lint")["structuredContent"] == {
        "code": "lint_refused",
        "message": "unreadable tickets",
        "paved_road": "restore ticket and repository readability, then retry clutch ticket lint",
    }
