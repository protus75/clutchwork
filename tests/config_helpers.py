"""Shared config, provider, rework and merge test scaffolding."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Shared test scaffolding for config, providers, Rework and merge: VALID and CONFIG fixtures, a scripted FakeExec, provider session and LLM builders, claude and codex JSONL replies, Rework order, requisition and successor helpers, MigrationFS, the repo fixture and stage context, and a bootstrap inline-admission check
# relates: [clutch/__main__.py, clutch/artifacts.py, clutch/config.py, clutch/driver.py, clutch/journal.py, clutch/llm.py, clutch/mergequeue.py]
# owner: engine
# verified: 38957300
# hash: 903b200961d48d421acbfb8ccf82e5d70e8b23c52b8623e53a315751cb7965e3

import asyncio
import dataclasses
import json
import textwrap
from datetime import UTC, datetime
from pathlib import Path

import pytest

from clutch import runner
from clutch.artifacts import Finding
from clutch.config import load_config
from clutch.driver import Driver
from clutch.journal import EventType, Journal
from clutch.llm import FakeLLM, LLMRequest
from clutch.mergequeue import CONFLICT_FACTS, MergeQueue
from clutch.providers import ProviderLLM, ProviderSession
from clutch.rework import rework
from clutch.seams import LocalFileSystem
from clutch.stages import StageContext
from clutch.tickets import ticket_path, validate_ticket
from clutch.timers import Timers
from tests.config_fixture import build_config
from tests.fakes import FakeClock, FakeFileSystem, FakeJournal, turn
from tests.fakes import FakeExec as SharedExec
from tests.git_fake import GitFake
from tests.stage_replies import requisition_reply
from tests.stages_helpers import CONFIG as STAGES_CONFIG
from tests.stages_helpers import ENV as STAGES_ENV
from tests.stages_helpers import SPECS, STEM, TICKET, adopt_conduct, agent, author, verdict

VALID = textwrap.dedent(
    """\
    schema_version: 1
    state_dir: .clutch
    providers:
      - name: claude
        kind: cli
        package: test-cli
        models_by_tier: {low: haiku, medium: sonnet, high: opus, max: opus}
        limits: {concurrency: 1, est_cost_per_call_usd: 0.25}
    routing:
      - {tier: medium, surface: implement, candidates: [{provider: claude, model: sonnet}]}
    review:
      mechanical:
        - {code: pytest, argv: [uv, run, pytest], trigger: always, severity: hard}
        - {code: ruff, argv: [uv, run, ruff, check], trigger: [clutch/], severity: soft}
      gate_severity: {scope_fence: hard}
    merge:
      safety_checks: [pytest]
      strategies:
        - {paths: [uv.lock], strategy: regenerate, argv: [uv, lock]}
        - {paths: [CHANGELOG.md], strategy: union}
    engine_plane_safety_inventory: [specs/, clutch/gates.py, config.yaml]
    """
)


CONFIG = build_config(
    state_dir="state",
    providers=[
        {"name": "claude", "auth": "CLAUDE_KEY", "models": {"low": "c-low", "medium": "c-med", "high": "c-high", "max": "c-max"}, "limits": {"concurrency": 1}},
        {"name": "codex", "auth": "CODEX_KEY", "models": {"low": "x-low", "medium": "x-med", "high": "x-high", "max": "x-max"}, "limits": {"concurrency": 1, "est_cost_per_call_usd": 1.5}},
    ],
    routing=[
        {"tier": "medium", "surface": "implement", "candidates": [{"provider": "codex"}, {"provider": "claude"}]},
        {"tier": "high", "surface": "implement", "candidates": [{"provider": "claude"}]},
        {"tier": "medium", "surface": "review", "candidates": [{"provider": "claude", "model": "c-max"}, {"provider": "codex"}]},
        {"tier": "low", "surface": "review", "candidates": [{"provider": "codex"}]},
    ],
    inventory=(),
)


ENV = {"PATH": "/usr/bin", "HOME": "/home/op", "CLAUDE_KEY": "sk-claude-secret", "CODEX_KEY": "sk-codex-secret"}


def config(tmp_path: Path, text: str = CONFIG):
    (tmp_path / "config.yaml").write_text(text)
    return load_config(None, cwd=tmp_path)


class FakeExec:
    """Scripted subprocess: records each invocation and what its stdin file held at spawn."""

    def __init__(self, *responses: tuple[int, str, str]) -> None:
        self.responses = list(responses)
        self.calls: list[dict] = []
        self.killed: list[int] = []
        self.hang: asyncio.Event | None = None

    async def run(self, argv, *, cwd, env, timeout, stdin_path=None, on_spawn=None, on_stdout_line=None, on_rusage=None):
        if argv[0] == "git":
            return 0, "a" * 40 + "\n", ""
        self.calls.append({"argv": list(argv), "cwd": cwd, "env": dict(env), "stdin": Path(stdin_path).read_text(), "timeout": timeout})
        if on_spawn is not None:
            on_spawn(4242)
        if self.hang is not None:
            await self.hang.wait()
            return -9, "", "killed"
        result = self.responses.pop(0)
        if on_stdout_line is not None:
            for line in result[1].splitlines(keepends=True):
                on_stdout_line(line)
        return result

    def kill_group(self, pgid: int) -> None:
        self.killed.append(pgid)
        if self.hang is not None:
            self.hang.set()


def provider_session(cfg, clock=lambda: datetime(2026, 1, 1, tzinfo=UTC), sleep=asyncio.sleep):
    journal = Journal(cfg.state_dir, clock)
    return ProviderSession(cfg, journal=journal, clock=clock, sleep=sleep, timers=Timers(journal=journal, clock=clock, sleep=sleep))


def llm(cfg, exec_: FakeExec, tmp_path: Path) -> ProviderLLM:
    return ProviderLLM(cfg, exec_=exec_, fs=LocalFileSystem(), env=ENV, cwd=tmp_path / "checkout", timeout=600, session=provider_session(cfg))


def req(surface: str, tier="medium", worktree=None, rendered="do the thing", effort="high") -> LLMRequest:
    return LLMRequest(surface=surface, rendered=rendered, tier=tier, effort=effort, ticket="t-1", worktree=worktree)


def jsonl(*events: dict) -> str:
    return "".join(json.dumps(e) + "\n" for e in events)


def claude_ok(text="done", cost=0.42) -> str:
    return jsonl(
        {"type": "system", "subtype": "init"},
        {"type": "assistant", "message": {"content": [{"type": "text", "text": "working"}]}},
        {
            "type": "result",
            "subtype": "success",
            "is_error": False,
            "result": text,
            "total_cost_usd": cost,
            "usage": {
                "input_tokens": 10,
                "cache_creation_input_tokens": 5,
                "cache_read_input_tokens": 100,
                "output_tokens": 7,
            },
        },
    )


def codex_ok(text="patched") -> str:
    return jsonl(
        {"type": "thread.started", "thread_id": "th"},
        {"type": "turn.started"},
        {"type": "item.completed", "item": {"id": "i0", "type": "agent_message", "text": "first"}},
        {"type": "item.completed", "item": {"id": "i1", "type": "command_execution", "command": "ls"}},
        {"type": "item.completed", "item": {"id": "i2", "type": "agent_message", "text": text}},
        {"type": "turn.completed", "usage": {"input_tokens": 300, "cached_input_tokens": 200, "output_tokens": 40}},
    )


def provider_request(name, tmp_path, **kwargs):
    return req("implement", tier="high" if name == "claude" else "medium", worktree=tmp_path, **kwargs)


run = asyncio.run


SNAG = Finding(code="scope", path="clutch/thing.py", line=1, message="narrow the work", paved_road="retain only the first buildable piece", kind="authoring_error")


async def original(ctx, *, source="human", payload=""):
    text = TICKET.format(bypass="agent_tier: high\nagent_effort: low\n").replace("source: human", f"source: {source}")
    text = text.replace("`thing.py` holds the word ok.", "`thing.py` holds the word ok." + payload)
    ctx.fs.write(ctx.repo / ticket_path("original"), text.encode())
    from tests.daemon_helpers import commit

    await commit(ctx, ctx.repo, [ticket_path("original")])
    return validate_ticket("original", text, ctx.repo), text


def order(action="escalate", proposals=()):
    return json.dumps({"action": action, "tickets": [{"stem": stem, "ticket": text} for stem, text in proposals]})


def requisition(verdict="approve", finding=SNAG):
    return requisition_reply(verdict, [] if verdict == "approve" else [finding.model_dump()])


async def invoke(ctx, ticket, text, script, *, attempt=0, workspace=None, snags=None):
    ctx.driver.llm = FakeLLM(script)
    result = await rework(ctx, ticket, text, snags or [SNAG], attempt=attempt, workspace=workspace or ctx.repo, tier="max", effort="medium", stuck_budget=42.0)
    return result, ctx.driver.llm.requests


def signals(ctx, signal=None):
    return [e for e in ctx.driver.journal.read() if e.type == EventType.SIGNAL and (signal is None or e.body.get("signal") == signal)]


def ticket_bytes(ctx):
    return {str(p.relative_to(ctx.repo)): data for p, data in ctx.fs.files.items() if p.is_relative_to(ctx.repo / "tickets")}


def successors(text, *, second_dep="piece-one"):
    first = text.replace("`thing.py` holds the word ok.", "First portion of `thing.py` holds ok.")
    second = text.replace("`thing.py` holds the word ok.", "Second portion of `thing.py` holds ok.")
    second = second.replace("## Depends on\nnone", f"## Depends on\n- {second_dep}")
    return [("piece-one", first), ("piece-two", second)]


class MigrationFS(FakeFileSystem):
    def __init__(self):
        super().__init__()
        self.writes = []

    def write(self, path, data):
        self.writes.append((path, data))
        super().write(path, data)


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    (root / "clutch").mkdir(parents=True)
    (root / "clutch" / "thing.py").write_text("")
    (root / "clutch" / "other.py").write_text("")
    (root / "CLUTCH_PLAN.md").write_text("# Plan\n")
    (root / "config.yaml").write_text(STAGES_CONFIG)
    (root / ".gitignore").write_text(".clutch/\n")
    adopt_conduct(root)
    return root


def context(repo: Path, script: list) -> StageContext:
    cfg = load_config(None, cwd=repo)
    clock = FakeClock(datetime(2026, 10, 5, tzinfo=UTC))

    async def sleep(seconds):
        clock.advance(seconds)
        await turn()

    journal = FakeJournal(clock)
    driver = Driver.from_config(cfg, journal=journal, llm=FakeLLM(script), env=STAGES_ENV, clock=clock, sleep=sleep)
    return StageContext(repo=repo, config=cfg, env=STAGES_ENV, exec_=SharedExec(), git=GitFake(), fs=FakeFileSystem(), driver=driver, specs_dir=SPECS)


WATCH_GIT = None


def watch_fixture_repo(tmp_path: Path, state_dir: str) -> Path:
    global WATCH_GIT
    root = tmp_path / "repo"
    root.mkdir()
    (root / "config.yaml").write_text(VALID.replace("state_dir: .clutch", f"state_dir: {state_dir}"))
    (root / "tickets").mkdir()
    WATCH_GIT = GitFake(rev_parse="fixture", merged_subjects=["fixture"])
    return root


def bootstrap_pipeline_keeps_inline_admission(repo, monkeypatch, verb):
    author(repo)
    source = context(repo, [])
    checkout = runner.Checkout(repo, source.config, source.env, source.exec_, source.git, source.driver.journal, source.fs, source.driver.clock, source.driver.sleep)
    from clutch.__main__ import build_control

    checkout = dataclasses.replace(checkout, control=build_control(checkout))
    llm = FakeLLM([agent({"clutch/thing.py": "ok\n"}), verdict()])

    def forbidden(*args, **kwargs):
        pytest.fail("bootstrap dispatch used the composed queue")

    monkeypatch.setattr(MergeQueue, "offer", forbidden)
    monkeypatch.setattr(MergeQueue, "process", forbidden)
    calls = []
    original = runner.merge

    async def inline(ctx, ticket, *, attempt):
        calls.append((ctx, ticket, attempt))
        return await original(ctx, ticket, attempt=attempt)

    monkeypatch.setattr(runner, "merge", inline)

    def pipeline(local):
        dispatch = runner.bind(local, llm)
        dispatch.queue.paused, dispatch.queue.hold_id = True, "daemon-only-hold"
        local.control.hold(dispatch.queue.hold_id)
        return dispatch

    ticket = validate_ticket(STEM, (repo / "tickets" / STEM / "ticket.md").read_text(), repo)
    if verb == "bind":
        assert asyncio.run(pipeline(checkout)(ticket)) == "merged"
    else:
        from tests.cli_helpers import cli

        assert cli(repo, *(["engine", "run", STEM] if verb == "run" else ["engine", "drain"]), stages=pipeline) == 0
    [(ctx, original_ticket, attempt)] = calls
    assert original_ticket.stem == ticket.stem and attempt == 0
    assert len([e for e in ctx.driver.journal.read() if e.type == EventType.STATE_TRANSITION and e.body.get("to") == "merged"]) == 1
    assert not any(e.body.get("kind") == CONFLICT_FACTS for e in ctx.driver.journal.read())
    assert (repo / "clutch/thing.py").read_text() == "ok\n" and not ctx.worktree(STEM).exists()
