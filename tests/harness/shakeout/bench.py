"""Disposable production composition for the shakeout battery."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: fixture
# purpose: Disposable production composition for the shakeout battery: a git-backed bench repo with fake-provider config, advancing clock, scripted LLM and drain entry.
# relates: [clutch/__main__.py, clutch/config.py, clutch/drain.py, clutch/git.py, clutch/hostfiles.py, clutch/journal.py, clutch/llm.py, clutch/providers.py]
# owner: engine
# verified: 6f94fa01
# hash: 83fe87d5e20b8d716c3ddd11a8220caeb5254e5a7d532f69d7093aa3cecfcb39

import asyncio
import os
from collections.abc import Mapping
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

import yaml

from clutch.__main__ import build_control
from clutch.config import Config, load_config
from clutch.drain import Report, drain
from clutch.git import Git
from clutch.hostfiles import render
from clutch.journal import Journal
from clutch.llm import LLM, FakeLLM, ScriptItem
from clutch.providers import ProviderLLM, routed_conduct_paths
from clutch.runner import Checkout, Dispatch, bind, pipeline
from clutch.seams import LocalFileSystem, SubprocessExec
from tests.config_fixture import build_config
from tests.integration.test_git import commit_lock

_CONFIG = build_config(
    providers=[{"name": "fake", "models": {"low": "fake", "medium": "fake", "high": "fake", "max": "fake"}, "limits": {"concurrency": 1, "est_cost_per_call_usd": 0.0}}],
    routing=[{"tier": "medium", "surface": "implement", "candidates": [{"provider": "fake"}]}, {"tier": "medium", "surface": "review", "candidates": [{"provider": "fake"}]}],
)


class AdvancingClock:
    def __init__(self) -> None:
        self.now = datetime(2026, 1, 1, tzinfo=UTC)

    def __call__(self) -> datetime:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += timedelta(seconds=seconds)


class Bench:
    def __init__(self, root: Path, llm: LLM | None = None) -> None:
        self.repo = Path(root)
        self.repo.mkdir(parents=True)
        self.fs = LocalFileSystem()
        self.fs.write(self.repo / "config.yaml", _CONFIG.encode())
        self.fs.write(self.repo / ".gitignore", b".clutch/\n")
        self.config = load_config(None, cwd=self.repo)
        self.clock = AdvancingClock()
        self._sleep_wake = asyncio.Event()
        self.process = SubprocessExec()
        self.env: Mapping[str, str] = {
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "HOME": str(self.repo),
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_AUTHOR_NAME": "shakeout",
            "GIT_AUTHOR_EMAIL": "shakeout@example.invalid",
            "GIT_COMMITTER_NAME": "shakeout",
            "GIT_COMMITTER_EMAIL": "shakeout@example.invalid",
        }
        self.git = Git(self.process, env=self.env, timeout=30.0, commit_lock=commit_lock(root / ".clutch/state"))
        self.journal = Journal(self.config.state_dir, self.clock)
        self.llm = llm if llm is not None else FakeLLM([])
        self.report: Report | None = None
        self._initialized = False
        self._checkout = self._compose(self.config)

    async def initialize(self) -> None:
        conduct = routed_conduct_paths(load_config(None, cwd=self.repo), self.repo)
        changed = []
        for path in conduct:
            previous = path.read_bytes() if path.exists() else b""
            fresh = render(previous)
            if fresh != previous:
                self.fs.write(path, fresh)
                changed.append(path.name)
        if self._initialized:
            # Members can replace routing after their base exists; adopt those routes before dispatch.
            if changed:
                await self.git.add(self.repo, changed)
                await self.git.commit(self.repo, "bench routed conduct", only=changed)
            return
        await self.git.init(self.repo, branch="main")
        await self.git.add(self.repo, ["config.yaml", ".gitignore", *(p.name for p in conduct)])
        await self.git.commit(self.repo, "bench base")
        self._initialized = True

    def _compose(self, config: Config) -> Checkout:
        checkout = Checkout(repo=self.repo, config=config, env=self.env, exec_=self.process, git=self.git, journal=self.journal, fs=self.fs, clock=self.clock, sleep=self._sleep)
        return replace(checkout, control=build_control(checkout))

    async def _sleep(self, seconds: float) -> None:
        """Advance only when a fixture wakes the timer after its call has started."""
        await self._sleep_wake.wait()
        self._sleep_wake.clear()
        self.clock.advance(seconds)

    def advance_sleep(self) -> None:
        self._sleep_wake.set()

    def configure(self, parsed_config: Config) -> None:
        self.config = parsed_config.model_copy(update={"state_dir": self.config.state_dir, "worktree_root": self.config.worktree_root})
        self._checkout = self._compose(self.config)
        self.fs.write(self.repo / "config.yaml", yaml.safe_dump(self.config.model_dump(mode="json", exclude_none=True)).encode())

    def add_ticket(self, stem: str, text: str) -> None:
        self.fs.write(self.repo / "tickets" / stem / "ticket.md", text.encode())
        from tests.approval import approve

        approve(self.repo, stem, self.clock)

    def script(self, items: list[ScriptItem]) -> None:
        if not isinstance(self.llm, FakeLLM):
            raise TypeError("script requires the default FakeLLM")
        self.llm.script.extend(items)

    def _pipeline(self) -> Dispatch:
        self._checkout = replace(self._checkout, control=build_control(self._checkout))
        if isinstance(self.llm, ProviderLLM):
            return pipeline(self._checkout)
        return bind(self._checkout, self.llm)

    async def drain(self) -> Report:
        await self.initialize()
        dispatch = self._pipeline()
        self.report = await drain(self._checkout, dispatch, reexec=SubprocessExec())
        return self.report

    def segments(self):
        return self.journal.read_segments()
