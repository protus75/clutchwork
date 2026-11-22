"""Shared stage test scaffolding backed by the in-memory seams."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Shared stage-test scaffolding: fake-provider config, ticket and repo fixtures, a scripted agent, report contexts and a `run` helper that drives `run_stages` over in-memory seams.
# relates: [clutch/artifacts.py, clutch/config.py, clutch/driver.py, clutch/git.py, clutch/hostfiles.py, clutch/llm.py, clutch/providers.py, clutch/seams.py]
# owner: engine
# verified: 38957300
# hash: 2773926930abf4b37d3d29debe4d72d8a91f2a02da7f70926f8779606f4a2222

import asyncio
import shutil
from datetime import UTC, datetime
from pathlib import Path

import pytest

from clutch.artifacts import Artifact, NonBlank
from clutch.config import load_config
from clutch.driver import Driver
from clutch.git import GitError, blob_sha
from clutch.llm import FakeLLM, LLMRequest
from clutch.seams import LocalFileSystem
from clutch.stages import Evidence, StageContext, run_stages
from clutch.tickets import validate_ticket
from tests.cli_helpers import ENV as CLI_ENV
from tests.config_fixture import build_config
from tests.fakes import FakeClock, FakeExec, FakeJournal
from tests.stage_replies import implement_reply
from tests.stage_replies import review_verdict as verdict

SAMPLE_REPORT = "sample-report.json"


class SampleReport(Artifact):
    entries: list[NonBlank]


SPECS = Path(__file__).resolve().parents[1] / "clutch" / "specs"


SECRET = "sk-test-not-for-children"


ENV = {**CLI_ENV, "FAKE_KEY": SECRET}


CONFIG = build_config(
    providers=[{"name": "fake", "auth": "FAKE_KEY", "models": {"low": "m", "medium": "m", "high": "m", "max": "m"}, "limits": {"concurrency": 1, "est_cost_per_call_usd": 0.5}}],
    routing=[{"tier": "medium", "surface": "implement", "candidates": [{"provider": "fake"}]}, {"tier": "medium", "surface": "review", "candidates": [{"provider": "fake"}]}],
)


TICKET = """---
state: confirmed
source: human
priority: P2
kind: feature
{bypass}---

## Depends on
none

## Context
- clutch/thing.py

## Goal / Why
`thing.py` holds the word ok.

## Boundary contract
none
- reason: unchanged behavior

## Scope in / Scope out
In: thing. Out: the rest.

## Scope fence
- clutch/thing.py

## Acceptance criteria
1. `grep -q ok clutch/thing.py` exits 0.

## Verification
```
grep -q ok clutch/thing.py
env
```

## Definition of rejected
Needs a new dependency.

## Time budget
- expected: 10m
- stuck: 20m
"""


STEM = "add-thing"


def adopt_conduct(root: Path) -> list[str]:
    """Render each fixture's actual routes from its own project bytes before committing its base."""
    from clutch.hostfiles import render
    from clutch.providers import routed_conduct_paths

    paths = routed_conduct_paths(load_config(None, cwd=root), root)
    for path in paths:
        path.write_bytes(render(path.read_bytes() if path.exists() else b""))
    return [p.relative_to(root).as_posix() for p in paths]


SNAG = {"code": "logic", "path": "clutch/thing.py", "line": 1, "message": "wrong word", "paved_road": "write ok"}


def _report_bytes() -> str:
    return SampleReport(produced_by_spec_version=1, produced_at_sha="abc", entries=["one"]).model_dump_json()


def evidence(**kw) -> Evidence:
    base = dict(stem=STEM, head_sha="abc", claimed="ok", scope_fence=["clutch/"], changed_files=["clutch/a.py"], inserted_lines=1, verification=[], run_record=None)
    return Evidence(**{**base, **kw})


async def report_context(repo, *, verification=None, source=None, script=None):
    """A disposable producer whose report is written by real Verification, never by its agent."""
    from tests.config_helpers import context

    ctx = context(repo, script if script is not None else [agent({}), verdict()])
    ctx.fs.write(repo / "clutch/thing.py", b"ok\n")
    ctx.fs.write(repo / "source.json", (source if source is not None else _report_bytes()).encode())
    command = verification if verification is not None else f"cp source.json tickets/{STEM}/{SAMPLE_REPORT}"
    raw = TICKET.format(bypass="").replace("grep -q ok clutch/thing.py\nenv", command)
    ctx.fs.write(repo / f"tickets/{STEM}/ticket.md", raw.encode())
    await ctx.git.add(repo, ["clutch/thing.py", "source.json", f"tickets/{STEM}/ticket.md"])
    await ctx.git.commit(repo, "producer fixture")
    ticket = validate_ticket(STEM, raw, repo)
    return ctx, ticket


def git(root: Path, *args: str) -> str:
    from tests.cli_helpers import git_out

    return git_out(root, *args)


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    from tests.cli_helpers import git_fake

    root = tmp_path / "repo"
    (root / "clutch").mkdir(parents=True)
    (root / "clutch" / "thing.py").write_text("")
    (root / "config.yaml").write_text(CONFIG)
    (root / ".gitignore").write_text(".clutch/\n")
    adopt_conduct(root)
    git_fake(root)
    return root


def author(repo: Path, bypass: str = "") -> None:
    from tests.cli_helpers import git_fake

    path = repo / "tickets" / STEM / "ticket.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(TICKET.format(bypass=bypass))
    fake = git_fake(repo)
    fake.calls.append(("add", (repo, ["tickets"]), {}))
    fake.calls.append(("commit", (repo, f"clutch({STEM}): ticket"), {}))


def agent(files: dict[str, str], outcome: str = "ok"):
    def act(req: LLMRequest) -> str:
        from tests.cli_helpers import git_fake

        assert req.worktree is not None
        for rel, text in files.items():
            (req.worktree / rel).parent.mkdir(parents=True, exist_ok=True)
            (req.worktree / rel).write_text(text)
        if files:
            fake = git_fake(req.worktree)
            fake.calls.append(("add", (req.worktree, list(files)), {}))
            fake.calls.append(("commit", (req.worktree, "work"), {}))
        return implement_reply(outcome)

    return act


def run(repo: Path, script: list, bypass: str = ""):
    from tests.cli_helpers import _git_fakes, git_fake

    author(repo, bypass)
    config = load_config(None, cwd=repo)
    llm = FakeLLM(script)
    clock = FakeClock(datetime(2026, 10, 5, tzinfo=UTC))
    fake = git_fake(repo)
    ticket_path = repo / "tickets" / STEM / "ticket.md"
    sha = blob_sha(ticket_path.read_bytes())

    def worktree_add(root, path, branch, start):
        shutil.copytree(root, path, ignore=shutil.ignore_patterns(".clutch"), dirs_exist_ok=True)
        _git_fakes[path] = fake

    def rev_parse(root, ref):
        if ref.startswith("HEAD:"):
            path = root / ref[5:]
            if path.is_file():
                return blob_sha(path.read_bytes())
            raise GitError(["git", "rev-parse", ref], 1, "", "missing")
        return sha

    def git_run(root, *args):
        if args[0] == "show" and args[1].startswith("HEAD:"):
            path = root / args[1][5:]
            if path.is_file():
                return path.read_text()
        raise GitError(["git", *args], 1, "", "missing")

    fake._overrides.update(rev_parse=rev_parse, _run=git_run, diff_names=["clutch/thing.py"], diff="+ok\n", commit="commit", worktree_add=worktree_add)

    async def never(seconds):
        await asyncio.Event().wait()

    driver = Driver.from_config(config, journal=FakeJournal(clock), llm=llm, env=ENV, clock=clock, sleep=never)
    ctx = StageContext(repo=repo, config=config, env=ENV, exec_=FakeExec(), git=fake, fs=LocalFileSystem(), driver=driver, specs_dir=SPECS)
    ticket = validate_ticket(STEM, ticket_path.read_text(), repo)
    return asyncio.run(run_stages(ctx, ticket)), llm, config
