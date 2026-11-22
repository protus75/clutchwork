# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Shared in-memory CLI test helpers moved out of tests/integration/test_cli.py: config, env, plan and ticket text, a cli() runner patched onto FakeExec and GitFake, git output, journal and write helpers.
# relates: [clutch/__main__.py, clutch/hostfiles.py, clutch/journal.py, clutch/llm.py, clutch/lockfile.py, clutch/runner.py, tests/config_fixture.py]
# owner: engine
# verified: ae1a5a3b
# hash: 81a807089403eb0e313ad39515df8a801c698f4be55f4b38ba17f6ac8b7f8e2f
from pathlib import Path
from unittest.mock import patch

import pytest

import clutch.__main__ as main_module
from clutch.journal import EventType
from clutch.lockfile import Lockfile, LockHeld
from tests.config_fixture import build_config
from tests.fakes import FakeClock as Clock
from tests.fakes import FakeExec, FakeJournal
from tests.git_fake import GitFake
from tests.integration.test_stages import adopt_conduct

ENV = {
    "PATH": "/usr/bin:/bin",
    "HOME": "/nonexistent",
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_AUTHOR_NAME": "t",
    "GIT_AUTHOR_EMAIL": "t@t",
    "GIT_COMMITTER_NAME": "t",
    "GIT_COMMITTER_EMAIL": "t@t",
}

CONFIG = build_config()

PLAN = "# Plan\n\n## 11. Failure spine\n\nSpine.\n"

TICKET = """---
priority: P2
kind: feature
---

## Depends on
{depends}

## Context
- clutch/thing.py

## Goal / Why
`thing()` returns ok.

## Boundary contract
none
- reason: unchanged behavior

## Scope in / Scope out
In: thing. Out: the rest.

## Scope fence
- clutch/thing.py

## Acceptance criteria
1. `uv run pytest` exits 0.

## Verification
```
uv run pytest
```

## Definition of rejected
Needs a new dependency.

## Time budget
- expected: 10m
- stuck: 20m
"""


def ticket(depends: str = "none") -> str:
    return TICKET.format(depends=depends)


def with_retro_driver(checkout, dispatch):
    from clutch import runner
    from clutch.llm import FakeLLM

    dispatch.stages = runner.bind(checkout, FakeLLM(['{"proposals": []}'] * 10)).stages
    return dispatch


class Stages:
    """Scripted fake for the stage-dispatch seam: records each dispatched ticket and the lock state."""

    def __init__(self, terminal: str = "merged") -> None:
        self.terminal = terminal
        self.calls: list[str] = []
        self.lock_held: list[bool] = []
        self.checkout = None

    def __call__(self, checkout):
        self.checkout = checkout

        async def dispatch(t):
            self.calls.append(t.stem)
            contender = Lockfile(checkout.config.state_dir, verb="drain", instance_id="contender", clock=Clock())
            try:
                contender.acquire()
            except LockHeld:
                self.lock_held.append(True)
            else:
                contender.release()
                self.lock_held.append(False)
            checkout.journal.append(EventType.STATE_TRANSITION, {"to": self.terminal}, ticket=t.stem)
            return self.terminal

        return with_retro_driver(checkout, dispatch)


@pytest.fixture
def root(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    (root / "clutch").mkdir(parents=True)
    (root / "clutch" / "thing.py").write_text("")
    (root / "CLUTCH_PLAN.md").write_text(PLAN)
    (root / "config.yaml").write_text(CONFIG)
    (root / ".gitignore").write_text(".clutch/\n")
    adopt_conduct(root)
    from clutch.hostfiles import render

    (root / "AGENTS.md").write_bytes(render(b""))
    git_fake(root)
    return root


_git_fakes = {}


def git_fake(root) -> GitFake:
    if root not in _git_fakes:
        _git_fakes[root] = GitFake()
    return _git_fakes[root]


def git_out(root: Path, *args: str) -> str:
    git_fake(root).calls.append(("git_out", args, {}))
    return ""


def journal(root: Path) -> FakeJournal:
    return FakeJournal()


def cli(root: Path, *argv: str, stages=None) -> int:
    with patch.object(main_module, "SubprocessExec", FakeExec), patch.object(main_module, "Git", return_value=git_fake(root)):
        return main_module.main(list(argv), cwd=root, env=ENV, clock=Clock(), pipeline=stages or Stages())


def write(root: Path, stem: str, text: str) -> None:
    path = root / "tickets" / stem / "ticket.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def core_config(root, routes):
    import yaml

    config = yaml.safe_load(CONFIG)
    claude = config["providers"][0]
    # Both providers are declared even when only one is routed.
    config["providers"].append({**claude, "name": "codex", "package": "other-cli"})
    config["routing"] = [{"tier": tier, "surface": surface, "candidates": [{"provider": name} for name in names]} for tier, surface, names in routes]
    path = root / "config.yaml"
    path.write_text(yaml.safe_dump(config))
    return path
