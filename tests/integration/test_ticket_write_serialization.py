# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Tests that verdict, author and rework ticket writes hold the main-write and commit locks so intake never sees an intermediate stamp, plus lock release on callback failure, merge-squash lock ordering and check commands running outside the write locks.
# relates: [clutch/daemon.py, clutch/effects.py, clutch/git.py, clutch/llm.py, clutch/runner.py, clutch/seams.py, clutch/stages.py, clutch/tickets.py]
# owner: clutch/git.py
# verified: 92889fdb
# hash: 1be0c803ac7c70d61aed02e9cf60e273662b5976381a88d7501bad0dc2d26247
# ruff: noqa: E501
import asyncio
import json

import pytest

from clutch import daemon, runner
from clutch.git import Git
from clutch.llm import FakeLLM
from clutch.seams import LocalFileSystem, SubprocessExec
from clutch.tickets import intake, stamp
from clutch.triage import triage_pass
from tests.daemon_helpers import ctx
from tests.drain_helpers import commit_ticket, confirmed, make_root, pause_checkout
from tests.integration.test_author import _box, _failure, _routes, requisition_reply
from tests.integration.test_git import commit_lock
from tests.integration.test_rework import SNAG, order, original, requisition
from tests.integration.test_triage import author_reply, reply

pytestmark = pytest.mark.disk_io_skip


async def race(checkout, action, stem, monkeypatch, journal=None):
    """Pause the real writer after its edit, with deliberately different intermediate bytes."""
    git = checkout.git
    original_commit = git.commit_edit
    entered, release, waiting = asyncio.Event(), asyncio.Event(), asyncio.Event()
    path = checkout.repo / f"tickets/{stem}/ticket.md"
    expected = []

    async def intercepted(repo, message, *, only, edit):
        async def paused():
            await edit()
            expected.append(path.read_bytes())
            path.write_bytes(expected[-1] + b"\nintermediate stamp\n")
            entered.set()
            await asyncio.wait_for(release.wait(), 10)
            path.write_bytes(expected[-1])

        return await original_commit(repo, message, only=only, edit=paused)

    monkeypatch.setattr(git, "commit_edit", intercepted)
    other_lock = commit_lock(checkout.config.state_dir)

    async def sleep(delay):
        waiting.set()
        await asyncio.sleep(delay)

    other_lock._sleep = sleep
    other = Git(SubprocessExec(), env=checkout.env, timeout=30, commit_lock=other_lock)
    task = asyncio.create_task(action())
    await asyncio.wait_for(entered.wait(), 10)
    pending = asyncio.create_task(intake(checkout.repo, other, journal or checkout.journal, LocalFileSystem(), stems=None))
    await asyncio.wait_for(waiting.wait(), 10)
    assert not pending.done()
    release.set()
    result = await asyncio.wait_for(task, 20)
    swept = await asyncio.wait_for(pending, 20)
    assert swept.committed == () and swept.refused == {}
    assert (await other._run(checkout.repo, "show", f"HEAD:tickets/{stem}/ticket.md")).encode() == expected[0]
    assert path.read_bytes() == expected[0]
    return result, expected[0]


@pytest.mark.parametrize("kill", [False, True])
def test_verdict_does_not_expose_stamp_to_intake(tmp_path, monkeypatch, kill):
    root = make_root(tmp_path)
    text = confirmed().replace("state: confirmed", "state: draft")
    commit_ticket(root, "target", text)
    checkout = pause_checkout(root)

    async def scenario():
        result, actual = await race(checkout, lambda: runner.verdict_locked("target", checkout, kill=kill), "target", monkeypatch)
        assert result == 0
        assert actual == stamp(text, "state", "rejected" if kill else "confirmed").encode()

    asyncio.run(scenario())


def test_author_does_not_expose_stamp_to_intake(tmp_path, monkeypatch):
    root = make_root(tmp_path)
    _routes(root)
    box = _box(root)
    _failure(box)
    checkout = pause_checkout(root)
    llm = FakeLLM([reply("author"), author_reply("authored"), requisition_reply("approve")])

    async def scenario():
        original_call = llm.call
        observed = []

        async def call(request):
            async with checkout.git.main_write():
                async with commit_lock(checkout.config.state_dir):
                    observed.append(request.surface)
            return await original_call(request)

        monkeypatch.setattr(llm, "call", call)
        _, actual = await race(checkout, lambda: triage_pass(checkout, llm), "authored", monkeypatch)
        assert "author" in observed and "requisition_review" in observed
        proposed = json.loads(author_reply("authored"))["ticket"]
        assert actual == stamp(stamp(proposed, "source", "box:failure_report"), "state", "draft").encode()

    asyncio.run(scenario())


def test_rework_does_not_expose_stamp_to_intake(ctx, monkeypatch):
    async def scenario():
        ticket, text = await original(ctx)
        ctx.worktree(ticket.stem).mkdir(parents=True)
        revised = text.strip().replace("`thing.py` holds the word ok.", "Narrowed `thing.py` holds ok.")
        ctx.driver.llm = FakeLLM([order("update", [(ticket.stem, revised)]), requisition()])
        result, actual = await race(ctx, lambda: daemon.apply_rework(ctx, ticket, [SNAG], attempt=0), ticket.stem, monkeypatch, ctx.driver.journal)
        assert result.outcome == "ok", result.findings
        assert actual == revised.encode()

    asyncio.run(scenario())


def test_callback_failure_releases_both_locks_and_effect_replays(tmp_path):
    from clutch.effects import Effects

    root = make_root(tmp_path)
    checkout = pause_checkout(root)
    path = root / "clutch/thing.py"
    effects = Effects(checkout.journal)
    calls = []

    async def scenario():
        async def fail():
            raise ValueError("edit failed")

        with pytest.raises(ValueError, match="edit failed"):
            await checkout.git.commit_edit(root, "failure", only=["clutch/thing.py"], edit=fail)

        async def edit():
            calls.append("edit")
            path.write_text("exact committed bytes\n")

        async def publish():
            return await checkout.git.commit_edit(root, "published", only=["clutch/thing.py"], edit=edit)

        first = await asyncio.wait_for(effects.run(publish, key="ticket-plane/test", ticket=None), 10)
        second = await asyncio.wait_for(effects.run(publish, key="ticket-plane/test", ticket=None), 10)
        assert first == second
        assert calls == ["edit"]
        assert await checkout.git._run(root, "show", "HEAD:clutch/thing.py") == "exact committed bytes\n"

    asyncio.run(scenario())


def test_merge_squash_waits_for_commit_lock(tmp_path):
    root = make_root(tmp_path)
    checkout = pause_checkout(root)
    git = checkout.git

    async def scenario():
        worktree = tmp_path / "branch"
        await git.worktree_add(root, worktree, "feature", "main")
        (worktree / "clutch/thing.py").write_text("branch content\n")
        await git.add(worktree, ["clutch/thing.py"])
        await git.commit(worktree, "feature")
        waiting = asyncio.Event()
        lock = commit_lock(checkout.config.state_dir)

        async def sleep(delay):
            waiting.set()
            await asyncio.sleep(delay)

        git._commit_lock._sleep = sleep
        async with lock:
            task = asyncio.create_task(git.merge_squash(root, "feature", "squashed"))
            await asyncio.wait_for(waiting.wait(), 10)
            assert not task.done()
            assert await git._run(root, "show", "HEAD:clutch/thing.py") == ""
        await asyncio.wait_for(task, 10)
        assert await git._run(root, "show", "HEAD:clutch/thing.py") == "branch content\n"

    asyncio.run(scenario())


def test_check_command_runs_outside_write_locks(ctx, monkeypatch):
    from types import SimpleNamespace

    from clutch import stages

    async def scenario():
        ticket, _ = await original(ctx)
        ctx.worktree(ticket.stem).mkdir(parents=True)
        original_run = stages.run_host_command
        observed = []

        async def run(*args, **kwargs):
            async with ctx.git.main_write():
                async with commit_lock(ctx.config.state_dir):
                    observed.append("check")
            return await original_run(*args, **kwargs)

        monkeypatch.setattr(stages, "run_host_command", run)
        entry = SimpleNamespace(results=None, argv=("true",), code="proof", severity="hard")
        monkeypatch.setattr(stages, "triggered_hosts", lambda *args, **kwargs: [(0, entry)])
        reports, hard = await asyncio.wait_for(stages.check_hosts(ctx, ticket, [], 0), 10)
        assert observed == ["check"]
        assert len(reports) == 1 and reports[0].verdict == "pass" and hard == []

    asyncio.run(scenario())
