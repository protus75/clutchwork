# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Unit tests of the MCP server's tool and prompt catalog, tool routing to shared clutch functions (snapshot, status, stats, roadmap, wait_event, evidence, context_suggest, prompt), repo routing, error mapping, and shared prompt resolution.
# relates: [clutch/__main__.py, clutch/ask.py, clutch/box.py, clutch/context.py, clutch/journal.py, clutch/mcp.py, clutch/observe.py, clutch/runner.py]
# owner: engine
# verified: fbabb2aa
# hash: b3e0141f7f96ad76377c69d938596f7d49e55e39728e9d6e09886e0dcd73ce3a
from types import SimpleNamespace

import pytest

from clutch import ask, mcp, observe, runner
from tests.git_fake import GitFake


def test_schemas_and_prompts(tmp_path, monkeypatch):
    server = mcp.ClutchMCPServer(default_cwd=tmp_path)
    assert set(item["name"] for item in server.dispatch("tools/list", {})["tools"]) == {
        "clutch_snapshot",
        "clutch_status",
        "clutch_stats",
        "clutch_roadmap_status",
        "clutch_wait_event",
        "clutch_evidence_captures",
        "clutch_evidence_show",
        "clutch_context_suggest",
        "clutch_prompt",
        "clutch_ticket_new",
        "clutch_ticket_lint",
        "clutch_ticket_order",
        "clutch_ticket_confirm",
        "clutch_ticket_reject",
        "clutch_app_ticket_confirm",
        "clutch_app_ticket_reject",
        "clutch_box_suggest",
        "clutch_box_triage",
        "clutch_box_dismiss",
        "clutch_engine_start",
        "clutch_engine_control",
        "clutch_engine_retro",
    }
    prompts = server.dispatch("prompts/list", {})["prompts"]
    assert {p["name"] for p in prompts} == set(ask.KINDS)
    assert next(p for p in prompts if p["name"] == "author")["arguments"][-1] == {"name": "stem", "required": True}
    seen = []
    monkeypatch.setattr(server, "checkout", lambda repo: (SimpleNamespace(), None))
    monkeypatch.setattr(server, "prompt", lambda checkout, ctx, kind, stems: (seen.append((kind, stems)) or "rendered", None))
    for value, expected in [("a, b", ["a", "b"]), (["c", "d"], ["c", "d"])]:
        result = server.dispatch("prompts/get", {"name": "box", "arguments": {"ids": value}})
        assert result["messages"][0]["content"]["text"] == "rendered"
        assert seen[-1] == ("box", expected)
    with pytest.raises(mcp.InvalidParams):
        server.dispatch("prompts/get", {"name": "author", "arguments": {}})


def test_tools_use_shared_functions(tmp_path, monkeypatch):
    server = mcp.ClutchMCPServer(default_cwd=tmp_path, sleep=lambda _: None, monotonic=lambda: 13)
    cfg = SimpleNamespace(state_dir=tmp_path, snapshot_merged_limit=17, evidence=SimpleNamespace(warn_gb=1))
    fs = SimpleNamespace(read_bytes=lambda p: b"", size=lambda p: 0)
    checkout = SimpleNamespace(config=cfg, fs=fs, repo=tmp_path)
    monkeypatch.setattr(server, "checkout", lambda repo: (checkout, "context"))
    seen = []
    monkeypatch.setattr(observe, "snapshot", lambda ctx, **kw: seen.append((ctx, kw)) or {"rows": [1]})
    result = server.dispatch("tools/call", {"name": "clutch_snapshot", "arguments": {"all_merged": True}})
    assert result["structuredContent"] == {"rows": [1]}
    assert seen == [("context", {"merged_limit": None})]
    monkeypatch.setattr(mcp.events, "wait_once", lambda state, **kw: seen.append(kw) or ("next", ["event"], False))
    result = server.dispatch("tools/call", {"name": "clutch_wait_event", "arguments": {"cursor": "old", "timeout_seconds": 8}})
    assert result["structuredContent"] == {"cursor": "next", "events": ["event"], "timed_out": False}
    assert seen[-1]["cursor"] == "old" and seen[-1]["timeout"] == 8
    monkeypatch.setattr(server, "call_tool", lambda *args: (_ for _ in ()).throw(runner.Refusal("bad", "repair", code="test")))
    result = server.dispatch("tools/call", {"name": "clutch_snapshot"})
    assert result["isError"] and result["structuredContent"] == {"code": "test", "message": "bad", "paved_road": "repair"}


def test_invalid_repo(tmp_path):
    server = mcp.ClutchMCPServer(default_cwd=tmp_path)
    for repo in ("", str(tmp_path), str(tmp_path / "missing")):
        result = server.dispatch("tools/call", {"name": "clutch_snapshot", "arguments": {"repo": repo}})
        assert result["isError"] and result["structuredContent"]["code"] == "invalid_repo"


def test_tool_routes(tmp_path, monkeypatch):
    from dataclasses import dataclass
    from datetime import UTC, datetime

    server = mcp.ClutchMCPServer(default_cwd=tmp_path, clock=lambda: datetime(2026, 1, 2, tzinfo=UTC))
    cfg = SimpleNamespace(state_dir=tmp_path, snapshot_merged_limit=3, evidence=SimpleNamespace(warn_gb=1))
    fs = SimpleNamespace(read_bytes=lambda p: b"", size=lambda p: 0)
    checkout = SimpleNamespace(config=cfg, fs=fs, repo=tmp_path, journal=SimpleNamespace(read=lambda: ["event"]))
    monkeypatch.setattr(server, "checkout", lambda repo: (checkout, "ctx"))
    seen = []

    class Store:
        def __init__(self, *args):
            pass

        def captures(self, stem, attempt):
            return [(4, "output")]

        def get_capture(self, stem, attempt, name):
            if attempt is None:
                raise ValueError("missing attempt")
            return f"capture {name}".encode()

        def read_record(self, key, kind):
            if key == "missing":
                raise FileNotFoundError(key)
            return {"kind": kind}

        def read_normalized(self, key):
            return ([{"normalizer": "demo"}], 0)

    monkeypatch.setattr(mcp, "EvidenceStore", Store)
    monkeypatch.setattr(mcp.views, "show_lines", lambda start, end, normalized: ["rendered"])
    monkeypatch.setattr(mcp, "size_warning", lambda store, warn: "large")
    monkeypatch.setattr(mcp.context, "suggest_for_stem", lambda state, root, stem, **kw: seen.append(kw["connect"]) or ([("other", "reason")], [("section", "match")]))

    async def collect(checkout, events, now, window):
        if window == "3d":
            raise ValueError("corrupt invoice")
        return {"window": {"spec": window}}

    async def road(checkout):
        return ["ready"]

    monkeypatch.setattr(mcp.stats, "collect_stats", collect)
    monkeypatch.setattr(mcp.stats, "stats_tree", lambda value: ["tree"])
    monkeypatch.setattr(mcp.roadmap, "status", road)
    monkeypatch.setattr(server, "prompt", lambda checkout, ctx, kind, stems, name: ("rendered prompt", None))
    import clutch.__main__ as entry
    import clutch.status as status

    @dataclass
    class Projection:
        scorecard: str = "included"
        merged: tuple = ("done",)

    async def projection(checkout):
        return Projection()

    monkeypatch.setattr(entry, "_status", projection)
    monkeypatch.setattr(status, "render", lambda projection, short: "status text")

    def call(tool, **arguments):
        return server.dispatch("tools/call", {"name": "clutch_" + tool, "arguments": arguments})

    assert call("status")["structuredContent"]["scorecard"] == "included"
    short = call("status", short=True)["structuredContent"]
    assert "scorecard" not in short and short["evidence_warning"] == "large" and short["version"] == mcp.version("clutchwork")
    assert call("stats", window="2d")["structuredContent"] == {"window": {"spec": "2d"}}
    assert call("stats", tree=True)["structuredContent"] == {"window": "7d", "tree": ["tree"]}
    assert call("stats", window="bad")["structuredContent"]["code"] == "invalid_window"
    corrupt = call("stats", window="3d")
    assert corrupt["isError"] and corrupt["structuredContent"]["code"] == "ValueError"
    assert corrupt["structuredContent"]["message"] == "corrupt invoice"
    assert call("roadmap_status")["structuredContent"] == {"lines": ["ready"]}
    assert call("evidence_captures", stem="demo")["structuredContent"] == {"captures": [[4, "output"]]}
    assert call("evidence_captures", stem="demo", attempt=4, name="output")["structuredContent"] == {"capture": "capture output"}
    assert call("evidence_captures", stem="demo", name="output")["structuredContent"] == {"code": "capture_error", "message": "missing attempt", "paved_road": "choose an existing capture and attempt"}
    assert call("evidence_show", call_key="demo")["structuredContent"]["lines"] == ["rendered"]
    assert call("evidence_show", call_key="missing")["isError"]
    assert call("context_suggest", stem="demo")["structuredContent"]["files"] == [["other", "reason"]]
    assert seen == [server.connect]
    assert call("prompt", kind="author", stems=["demo"])["content"][0]["text"] == "rendered prompt"


def test_prompt_domain_and_validation(tmp_path, monkeypatch):
    server = mcp.ClutchMCPServer(default_cwd=tmp_path)
    with pytest.raises(mcp.InvalidParams):
        server.dispatch("prompts/get", {"name": "missing"})
    with pytest.raises(mcp.DomainError) as exc:
        server.dispatch("prompts/get", {"name": "author", "arguments": {"stem": "demo"}})
    assert exc.value.args[0]["code"] == "invalid_repo"
    with pytest.raises(mcp.InvalidParams):
        server.dispatch("prompts/get", {"name": "box", "arguments": {"ids": 7}})


def test_routing_and_config(tmp_path, monkeypatch):
    from tests.config_helpers import VALID

    first = tmp_path / "first"
    second = tmp_path / "second"
    for root in (first, second):
        (root / "tickets").mkdir(parents=True)
        (root / "config.yaml").write_text(VALID)
    seen = []
    monkeypatch.setattr(mcp, "Git", lambda *a, **kw: seen.append(kw["env"]) or object())
    server = mcp.ClutchMCPServer(default_cwd=first, git_factory=mcp.Git, env={})
    assert server.checkout(None)[0].repo == first
    assert server.checkout(str(second))[0].repo == second
    assert all(env["GIT_OPTIONAL_LOCKS"] == "0" for env in seen)
    (second / "config.yaml").unlink()
    result = server.dispatch("tools/call", {"name": "clutch_snapshot", "arguments": {"repo": str(second)}})
    assert result["isError"] and result["structuredContent"]["paved_road"]


def test_shared_prompt_resolution(tmp_path, monkeypatch):
    from pathlib import Path

    cfg = SimpleNamespace(state_dir=tmp_path / "state", prompts_dir=None, ask_notes=None)
    ticket = tmp_path / "tickets" / "demo" / "ticket.md"
    ticket.parent.mkdir(parents=True)
    ticket.write_text("body")
    seen = []
    monkeypatch.setattr(ask, "render", lambda kind, stem, config, repo: seen.append((kind, stem)) or f"{kind}:{stem}")

    def resolve(kind, stems=(), running=lambda: (), drafts=lambda: ("demo",)):
        return ask.resolve_prompt(kind, stems, config=cfg, repo=tmp_path, running_stems=running, draft_stems=drafts)

    assert resolve("author", ["new"])[0] == "author:new"
    assert resolve("diagnose", ["demo"], running=lambda: ["demo"])[0] == "running:demo"
    assert resolve("drafts")[0] == "drafts:('demo',)"
    assert resolve("box", ["box-1"])[0] == "box:['box-1']"
    assert len(resolve("list")[1]["entries"]) == len(ask.KINDS)
    for kind, stems in [("unknown", []), ("review", ["missing"]), ("drafts", ["demo"]), ("box", []), ("author", ["Bad_Stem"])]:
        with pytest.raises(runner.Refusal) as exc:
            resolve(kind, stems)
        assert exc.value.code and exc.value.message and exc.value.paved_road


def test_context_suggest_shared(tmp_path):
    from clutch import context

    ticket = tmp_path / "tickets" / "demo" / "ticket.md"
    ticket.parent.mkdir(parents=True)
    ticket.write_text("## Goal / Why\n`sample query`\n## Scope fence\n- source.py\n")
    state = tmp_path / "state"
    state.mkdir()
    (state / "index.duckdb").write_bytes(b"placeholder")
    from clutch.seams import LocalFileSystem

    calls = []

    class Result:
        def __init__(self, rows):
            self.rows = rows

        def fetchall(self):
            return self.rows

    class Connection:
        def execute(self, query, *args):
            if "FROM files" in query:
                return Result([("other.py",)])
            if "FROM chunks" in query:
                return Result([("other.py", "other.py#part", "sample query")])
            return Result([("past", "source.py"), ("past", "other.py")])

        def close(self):
            calls.append("closed")

    def connect(path, *, read_only):
        calls.append((path, read_only))
        return Connection()

    files, chunks = context.suggest_for_stem(state, tmp_path, "demo", fs=LocalFileSystem(), connect=connect)
    assert files == [("other.py", "changed with source.py in 1 past tickets")]
    assert chunks == [("other.py#part", "matches query, sample")]
    assert calls == [(str(state / "index.duckdb"), True), "closed"]
    for stem, code in [("decisions", "invalid_stem"), ("missing", "missing_ticket")]:
        with pytest.raises(runner.Refusal) as exc:
            context.suggest_for_stem(state, tmp_path, stem, fs=LocalFileSystem(), connect=connect)
        assert exc.value.code == code
    (state / "index.duckdb").unlink()
    with pytest.raises(runner.Refusal) as exc:
        context.suggest_for_stem(state, tmp_path, "demo", fs=LocalFileSystem(), connect=connect)
    assert exc.value.code == "no_index"


def test_invalid_wait_and_snapshot_limit(tmp_path, monkeypatch):
    cfg = SimpleNamespace(state_dir=tmp_path, snapshot_merged_limit=9)
    checkout = SimpleNamespace(config=cfg, fs=SimpleNamespace(read_bytes=None, size=None))
    server = mcp.ClutchMCPServer(default_cwd=tmp_path)
    monkeypatch.setattr(server, "checkout", lambda repo: (checkout, "ctx"))
    limits = []
    monkeypatch.setattr(observe, "snapshot", lambda ctx, *, merged_limit: limits.append(merged_limit) or {"rows": []})
    server.dispatch("tools/call", {"name": "clutch_snapshot"})
    assert limits == [9]

    def invalid(*args, **kwargs):
        raise ValueError("bad cursor")

    monkeypatch.setattr(mcp.events, "wait_once", invalid)
    response = server.dispatch("tools/call", {"name": "clutch_wait_event", "arguments": {"cursor": "bad"}})
    assert response["isError"] and response["structuredContent"] == {"code": "invalid_cursor_or_timeout", "message": "bad cursor", "paved_road": "supply a valid cursor and nonnegative timeout"}


def test_collect_stats_filters_invoices(tmp_path, monkeypatch):
    import asyncio
    from datetime import UTC, datetime

    from clutch import stats
    from clutch.journal import EventType
    from clutch.stages import Invoice

    now = datetime(2026, 1, 3, tzinfo=UTC)
    ticket = tmp_path / "tickets" / "demo" / "ticket.md"
    ticket.parent.mkdir(parents=True)
    ticket.write_text("---\nkind: bug\n---\n")

    def event(key, date, type=EventType.EFFECT_COMPLETION, stem="demo"):
        return SimpleNamespace(ticket=stem, type=type, key=key, ts=date, body={"result": {"commit": "abc"}})

    events = [
        event("ticket-plane/demo/1/checks", "2026-01-02T12:00:00+00:00"),
        event("ticket-plane/demo/2/checks", "2025-12-01T00:00:00+00:00"),
        event("ticket-plane/demo/3/checks", "2026-01-04T00:00:00+00:00"),
        event("ticket-plane/demo/4/notchecks", "2026-01-02T00:00:00+00:00"),
        event("ticket-plane/demo/5/checks", "2026-01-02T00:00:00+00:00", type=EventType.SIGNAL),
    ]

    calls, seen = [], []
    git_seam = GitFake(_run=lambda *args: calls.append(args) or "invoice")
    monkeypatch.setattr(Invoice, "model_validate_json", lambda text: "parsed invoice")
    monkeypatch.setattr(stats, "project_stats", lambda events, kinds, checks, **kwargs: seen.append((kinds, checks)) or "projection")
    result = asyncio.run(stats.collect_stats(SimpleNamespace(repo=tmp_path, git=git_seam), events, now, "2d"))
    assert result == "projection"
    assert calls == [(tmp_path, "show", "abc:tickets/demo/checks.json")]
    assert seen == [({"demo": "bug"}, {"ticket-plane/demo/1/checks": "parsed invoice"})]


def test_prompt_tool_renders_templates(tmp_path, monkeypatch):
    from clutch import box
    from clutch.seams import LocalFileSystem

    cfg = SimpleNamespace(state_dir=tmp_path / "state", prompts_dir=None, ask_notes=None)
    specs = tmp_path / "specs" / "ask"
    specs.mkdir(parents=True)
    for kind, template in [("author", "author $stem $ticket $state_dir"), ("running", "running $stem $state_dir"), ("drafts", "drafts $tickets $state_dir"), ("box", "box $messages")]:
        (specs / f"{kind}.md").write_text(template)
    monkeypatch.setattr(ask, "SPECS_DIR", specs.parent)
    ticket = tmp_path / "tickets" / "demo" / "ticket.md"
    ticket.parent.mkdir(parents=True)
    ticket.write_text("ticket")
    monkeypatch.setattr(observe, "journal", lambda state: [])
    monkeypatch.setattr(observe, "as_events", lambda history: [])
    monkeypatch.setattr(observe, "last_bodies", lambda history: {})
    monkeypatch.setattr(observe, "running_stems", lambda state, last: ["demo"])
    monkeypatch.setattr(observe, "snapshot", lambda ctx: {"rows": [{"stem": "demo", "draft": True}, {"stem": "other", "draft": False}]})

    class Box:
        def __init__(self, root, fs):
            self.root = root

        def get(self, id):
            return SimpleNamespace(id=id)

        def path(self, message):
            return self.root / f"{message.id}.json"

    monkeypatch.setattr(box, "Box", Box)
    server = mcp.ClutchMCPServer(default_cwd=tmp_path)
    checkout = SimpleNamespace(repo=tmp_path, config=cfg, fs=LocalFileSystem())
    monkeypatch.setattr(server, "checkout", lambda repo: (checkout, "ctx"))

    def render(kind, stems=()):
        return server.dispatch("tools/call", {"name": "clutch_prompt", "arguments": {"kind": kind, "stems": list(stems)}})["content"][0]["text"]

    assert render("author", ["new"]) == "author new tickets/new/ticket.md state"
    assert render("diagnose", ["demo"]) == "running demo state"
    assert render("drafts") == "drafts - demo: tickets/demo/ticket.md state"
    assert render("box", ["box-123"]) == "box - box-123: state/box/box-123.json"


def test_prompt_argument_catalog(tmp_path):
    server = mcp.ClutchMCPServer(default_cwd=tmp_path)
    entries = {entry["name"]: entry["arguments"] for entry in server.dispatch("prompts/list", {})["prompts"]}
    assert entries == {
        kind: [{"name": "repo", "required": False}]
        + ([{"name": "stem", "required": True}] if kind in {"diagnose", "running", "review", "author"} else [{"name": "ids", "required": True}] if kind == "box" else [])
        for kind in ("diagnose", "running", "review", "author", "box", "drafts", "drain-loop", "plan-ticket-drain", "plan-ticket-serve", "roadmap")
    }
