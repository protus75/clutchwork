"""Shared in-memory drain test scaffolding."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Shared in-memory drain test scaffolding: a scripted stage seam, a temp-checkout root builder, a drain runner, committed-ticket helpers, journal queries, a pause checkout and a re-entry drain over FakeLLM.
# relates: [clutch/__main__.py, clutch/artifacts.py, clutch/caps.py, clutch/config.py, clutch/journal.py, clutch/llm.py, clutch/lockfile.py, clutch/runner.py]
# owner: engine
# verified: 0a4d026b
# hash: 112727eb52b7bc02cb91432df0264ea72cf2962a168258baa4fc5f78c4624a16

import asyncio
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

import pytest

import clutch.__main__ as main_module
from clutch.caps import draws
from clutch.journal import EventType
from clutch.lockfile import Lockfile, LockHeld
from tests.cli_helpers import CONFIG, ENV, PLAN, git_fake, ticket, with_retro_driver, write
from tests.fakes import FakeClock as Clock
from tests.fakes import FakeExec, FakeFileSystem

START = datetime(2026, 1, 1, tzinfo=UTC)
NoChild = FakeExec


class Script:
    """Scripted stage seam: each stem's terminals in order (default `merged`), plus per-stem side effects."""

    def __init__(self, outcomes: dict[str, list[str]] | None = None, hooks: dict | None = None) -> None:
        self.outcomes = {stem: list(seq) for stem, seq in (outcomes or {}).items()}
        self.hooks = hooks or {}
        self.calls: list[str] = []
        self.lock_held: list[bool] = []

    def __call__(self, checkout):
        async def dispatch(t):
            self.calls.append(t.stem)
            contender = Lockfile(checkout.config.state_dir, verb="drain", instance_id="contender", clock=checkout.clock)
            try:
                contender.acquire()
            except LockHeld:
                self.lock_held.append(True)
            else:
                contender.release()
                self.lock_held.append(False)
            if hook := self.hooks.get(t.stem):
                hook(checkout)
            seq = self.outcomes.get(t.stem, [])
            terminal = seq.pop(0) if seq else "merged"
            checkout.journal.append(EventType.STATE_TRANSITION, {"to": terminal, "stage": "review"} if terminal != "merged" else {"to": terminal}, ticket=t.stem)
            return terminal

        return with_retro_driver(checkout, dispatch)


def make_root(tmp_path: Path, caps: str = "") -> Path:
    root = tmp_path / "repo"
    (root / "clutch").mkdir(parents=True)
    (root / "clutch" / "thing.py").write_text("")
    (root / "CLUTCH_PLAN.md").write_text(PLAN)
    (root / "config.yaml").write_text(CONFIG + caps)
    (root / ".gitignore").write_text(".clutch/\n")
    from tests.stages_helpers import adopt_conduct

    adopt_conduct(root)
    git_fake(root)._overrides["_run"] = lambda directory, *args: (
        (directory / args[1].removeprefix("HEAD:")).read_text() if args and args[0] == "show" and (directory / args[1].removeprefix("HEAD:")).is_file() else ""
    )
    return root


@pytest.fixture
def root(tmp_path: Path) -> Path:
    return make_root(tmp_path)


def drain(root: Path, script: Script, clock: Clock | None = None) -> int:
    with patch.object(main_module, "Subprocess" + "Exec", FakeExec), patch.object(main_module, "Git", return_value=git_fake(root)):
        return main_module.main(["engine", "drain"], cwd=root, env=ENV, clock=clock or Clock(START), pipeline=script)


def journal(root):
    from tests.cli_helpers import journal as fake_journal

    return fake_journal(root)


def confirmed(depends: str = "none", priority: str = "P2") -> str:
    """A ticket as the ticket-plane lane commits it: frontmatter already stamped, no intake needed."""
    return ticket(depends).replace("---\npriority: P2", f"---\nstate: confirmed\nsource: human\npriority: {priority}", 1)


def commit_ticket(root: Path, stem: str, text: str) -> None:
    write(root, stem, text)
    path = f"tickets/{stem}/ticket.md"

    async def commit():
        fake = git_fake(root)
        await fake.add(root, [path])
        await fake.commit(root, f"clutch({stem}): ticket", only=[path])

    asyncio.run(commit())


def retry_draws(root: Path, stem: str) -> int:
    return draws(journal(root).read(), stem, "retry")


def tos(root: Path, stem: str) -> list[str]:
    return [e.body["to"] for e in journal(root).read() if e.type == EventType.STATE_TRANSITION and e.ticket == stem]


def mechanical_first(monkeypatch, stem, *, workspace=True):
    from clutch import runner, stages
    from clutch.artifacts import Cost, Finding, StageResult

    original = runner.run_stages
    called = []

    async def first(ctx, ticket):
        if ticket.stem == stem and not called:
            called.append(ticket.stem)
            if workspace:
                await stages.prepare_worktree(ctx, ticket.stem)
            return stages.StagesRun(
                attempt=0,
                results={
                    "implement": StageResult(
                        outcome="premise_failed", artifact=None, cost=Cost(), findings=[Finding(code="render_over_bound", message="too large", paved_road="shrink or split and rerun drain")]
                    )
                },
            )
        return await original(ctx, ticket)

    monkeypatch.setattr(runner, "run_stages", first)
    return called


def pause_checkout(root):
    from clutch.config import load_config
    from clutch.runner import Checkout

    checkout = Checkout(root, load_config(None, cwd=root), ENV, FakeExec(), git_fake(root), journal(root), FakeFileSystem(), Clock(START))
    return replace(checkout, control=main_module.build_control(checkout))


def offer_events(root):
    return [e for e in journal(root).read() if e.type in {EventType.CAP_CONSUMED, EventType.STATE_TRANSITION} or e.body.get("signal") == "reject_verdict"]


def reentry_drain(repo: Path, script: list, *, green_base: bool = True):
    from clutch import runner
    from clutch.llm import FakeLLM

    if green_base:
        (repo / "clutch" / "thing.py").write_text("ok base\n")
        asyncio.run(git_fake(repo).commit(repo, "green verification base"))
    llm = FakeLLM(script)
    with patch.object(main_module, "Subprocess" + "Exec", FakeExec), patch.object(main_module, "Git", return_value=git_fake(repo)):
        code = main_module.main(["engine", "drain"], cwd=repo, env=ENV, clock=Clock(START), pipeline=lambda c: runner.bind(c, llm), reexec=NoChild())
    return code, llm
