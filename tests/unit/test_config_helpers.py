# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Tests that each shared helper in tests/config_helpers.py is importable and behaves as documented, from configs and fakes to repo, context and bootstrap pipeline helpers.
# relates: [clutch/__main__.py, clutch/config.py, clutch/journal.py, clutch/runner.py, tests/config_helpers.py, tests/fakes.py, tests/git_fake.py]
# owner: engine
# verified: 38957300
# hash: e6c69cb9b87b3c5c9e3fb8e1d815462250a4303803df11b5ec46e244d551e9ca
import asyncio
import json
from types import SimpleNamespace

import pytest

from clutch.config import load_config
from clutch.journal import EventType
from tests import config_helpers as h
from tests.fakes import FakeFileSystem, FakeJournal
from tests.git_fake import GitFake


def test_all_names_importable():
    names = "CONFIG ENV FakeExec MigrationFS SNAG VALID claude_ok codex_ok config context invoke jsonl llm order original provider_request provider_session repo req requisition run signals successors bootstrap_pipeline_keeps_inline_admission ticket_bytes watch_fixture_repo".split()
    assert all(getattr(h, name) is not None for name in names)


def test_valid(tmp_path):
    (tmp_path / "config.yaml").write_text(h.VALID)
    assert load_config(None, cwd=tmp_path).providers[0].models_by_tier.medium == "sonnet"


def test_config_text(tmp_path):
    assert h.config(tmp_path, h.CONFIG).providers[1].name == "codex"


def test_env():
    assert h.ENV["CLAUDE_KEY"] == "sk-claude-secret"


def test_config(tmp_path):
    assert h.config(tmp_path).state_dir == tmp_path / "state"


def test_fake_exec(tmp_path):
    stdin = tmp_path / "stdin"
    stdin.write_text("prompt")
    fake = h.FakeExec((0, "answer\n", ""))
    spawned, lines = [], []
    result = asyncio.run(fake.run(["agent"], cwd=tmp_path, env={}, timeout=3, stdin_path=stdin, on_spawn=spawned.append, on_stdout_line=lines.append))
    assert (result, spawned, lines, fake.calls[0]["stdin"]) == ((0, "answer\n", ""), [4242], ["answer\n"], "prompt")


def test_migration_fs(tmp_path):
    fs = h.MigrationFS()
    fs.write(tmp_path / "config", b"new")
    assert fs.read_bytes(tmp_path / "config") == b"new" and fs.writes == [(tmp_path / "config", b"new")]


def test_provider_session(tmp_path):
    session = h.provider_session(h.config(tmp_path))
    assert session.journal.dir == tmp_path / "state/journal"


def test_llm(tmp_path):
    fake = h.FakeExec()
    assert h.llm(h.config(tmp_path), fake, tmp_path)._exec is fake


def test_req():
    request = h.req("review", tier="low", rendered="inspect")
    assert (request.surface, request.tier, request.rendered) == ("review", "low", "inspect")


def test_provider_request(tmp_path):
    request = h.provider_request("claude", tmp_path, rendered="inspect")
    assert (request.tier, request.worktree, request.rendered) == ("high", tmp_path, "inspect")


def test_jsonl():
    assert h.jsonl({"a": 1}, {"b": 2}) == '{"a": 1}\n{"b": 2}\n'


def test_claude_ok():
    result = json.loads(h.claude_ok("specific", 1.25).splitlines()[-1])
    assert (result["result"], result["total_cost_usd"]) == ("specific", 1.25)


def test_codex_ok():
    assert json.loads(h.codex_ok("specific").splitlines()[-2])["item"]["text"] == "specific"


def test_snag():
    assert (h.SNAG.code, h.SNAG.path) == ("scope", "clutch/thing.py")


def test_run():
    async def value():
        return 17

    assert h.run(value()) == 17


def test_original(tmp_path):
    (tmp_path / "clutch").mkdir()
    (tmp_path / "clutch/thing.py").write_text("fixture")
    ctx = SimpleNamespace(repo=tmp_path, fs=FakeFileSystem(), git=GitFake())
    ticket, text = asyncio.run(h.original(ctx, source="seed", payload=" EXTRA"))
    assert ticket.stem == "original" and "source: seed" in text and " EXTRA" in text
    assert [call[0] for call in ctx.git.calls] == ["add", "commit"]


def test_order():
    assert json.loads(h.order("split", [("one", "contents")])) == {"action": "split", "tickets": [{"stem": "one", "ticket": "contents"}]}


def test_requisition():
    assert json.loads(h.requisition("reject"))["findings"][0]["message"] == "narrow the work"


def test_invoke(monkeypatch, tmp_path):
    captured = {}

    async def fake(ctx, ticket, text, snags, **kwargs):
        captured.update(kwargs)
        return "result"

    monkeypatch.setattr(h, "rework", fake)
    ctx = SimpleNamespace(repo=tmp_path, driver=SimpleNamespace())
    result, requests = asyncio.run(h.invoke(ctx, "ticket", "text", [], attempt=3))
    assert (result, requests, captured["attempt"], captured["workspace"]) == ("result", [], 3, tmp_path)


def test_signals():
    journal = FakeJournal()
    journal.append(EventType.SIGNAL, {"signal": "wanted"})
    journal.append(EventType.SIGNAL, {"signal": "other"})
    ctx = SimpleNamespace(driver=SimpleNamespace(journal=journal))
    assert [e.body["signal"] for e in h.signals(ctx, "wanted")] == ["wanted"]


def test_ticket_bytes(tmp_path):
    fs = FakeFileSystem()
    fs.write(tmp_path / "tickets/a/ticket.md", b"first")
    fs.write(tmp_path / "other", b"second")
    assert h.ticket_bytes(SimpleNamespace(repo=tmp_path, fs=fs)) == {"tickets/a/ticket.md": b"first"}


def test_successors():
    first, second = h.successors("## Depends on\nnone\n`thing.py` holds the word ok.", second_dep="alternate")
    assert first[0] == "piece-one" and "First portion" in first[1] and "- alternate" in second[1]


def test_repo(tmp_path):
    root = h.repo.__wrapped__(tmp_path)
    assert (root / "config.yaml").read_text() == h.STAGES_CONFIG and not (root / ".git").exists()


def test_context(tmp_path):
    root = h.repo.__wrapped__(tmp_path)
    ctx = h.context(root, [])
    assert isinstance(ctx.git, GitFake) and isinstance(ctx.fs, FakeFileSystem) and isinstance(ctx.driver.journal, FakeJournal)


def test_watch_fixture_repo(tmp_path):
    root = h.watch_fixture_repo(tmp_path, "state")
    assert "state_dir: state\n" in (root / "config.yaml").read_text()
    assert (root / "tickets").is_dir() and not (root / ".git").exists()
    assert isinstance(h.WATCH_GIT, GitFake) and h.WATCH_GIT.calls == []
    assert asyncio.run(h.WATCH_GIT.rev_parse(root, "HEAD")) == "fixture"


def test_bootstrap_pipeline_keeps_inline_admission(tmp_path, monkeypatch):
    from clutch import __main__ as main_module
    from clutch import runner

    root = h.repo.__wrapped__(tmp_path)
    source = h.context(root, [])
    monkeypatch.setattr(h, "context", lambda repo, script: source)
    control = SimpleNamespace(hold=lambda value: None)
    monkeypatch.setattr(main_module, "build_control", lambda checkout: control)

    async def merge(ctx, ticket, *, attempt):
        (root / "clutch/thing.py").write_text("ok\n")
        ctx.driver.journal.append(EventType.STATE_TRANSITION, {"to": "merged"})
        return "merged"

    monkeypatch.setattr(runner, "merge", merge)

    def bind(checkout, llm):
        async def dispatch(ticket):
            return await runner.merge(source, ticket, attempt=0)

        dispatch.queue = SimpleNamespace(paused=False, hold_id=None)
        return dispatch

    monkeypatch.setattr(runner, "bind", bind)
    h.bootstrap_pipeline_keeps_inline_admission(root, monkeypatch, "bind")
    assert (root / "clutch/thing.py").read_text() == "ok\n"
