"""Boundaries and model repair use only injected seams."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Model conflict resolution: eligibility bounds (files, markers, binary, rename, inventory), resolve-then-review paths, and merge stage restore after a nested resolution
# relates: [clutch/artifacts.py, clutch/driver.py, clutch/mergequeue.py, clutch/specs/__init__.py, clutch/stages.py]
# owner: engine
# verified: 452057e3
# hash: 269896e37a3195f4e0b33686fd1c5ff183adadc89d8bbb92ee456bd1f4bde696

import asyncio
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from clutch import mergequeue, stages
from clutch.artifacts import Cost, StageResult
from clutch.mergequeue import MergeQueue, ResolveReply, model_eligible
from clutch.specs import data_close, data_open, load_spec
from tests.git_fake import GitFake


def files(n=1):
    return {f"src/{i}": ("base", "main", "ticket") for i in range(n)}


def test_file_bound():
    # A limit of two refuses three; four or unlimited admits four.
    assert model_eligible(files(3), {}, [], [])
    assert not model_eligible(files(4), {}, [], [])


def test_marker_bound():
    # Counting per-file instead of globally admits 61 across these two paths.
    assert model_eligible(files(2), {"src/0": "=======\n" * 30, "src/1": "=======\n" * 30}, [], [])
    assert not model_eligible(files(2), {"src/0": "=======\n" * 30, "src/1": "=======\n" * 31}, [], [])


@pytest.mark.parametrize("contents", [("a\0", "b", "c"), ("a", "b\0", "c"), ("a", "b", "c\0"), (None, "b", "c"), ("a", None, "c"), ("a", "b", None)])
def test_binary_and_missing_stage(contents):
    # Skipping any index stage would admit its binary or missing version.
    assert not model_eligible({"src/0": contents}, {}, [], [])


def test_rename_and_inventory():
    # A rename with otherwise eligible stages must still refuse.
    assert not model_eligible(files(), {}, [], [], ["src/0"])
    # Ignoring the inventory would admit this ordinary text conflict.
    assert not model_eligible(files(), {}, ["src/"], [])


def test_shared_waives_only_inventory():
    # Shared exemption must neither be ignored nor bypass the other bounds.
    assert model_eligible(files(3), {}, ["src"], ["src"])
    assert not model_eligible(files(4), {}, ["src"], ["src"])
    assert not model_eligible(files(), {"src/0": "=======\n" * 61}, ["src"], ["src"])
    assert not model_eligible({"src/0": ("a", "b\0", "c")}, {}, ["src"], ["src"])


def rig(monkeypatch, replies):
    writes, signals, prompts = {}, [], []

    async def git_run(root, *args):
        if args[0] == "log":
            return "clutch(other): sibling\noperator commit\nclutch(other): duplicate\n"
        if args[:2] == ("show", "main:tickets/other/ticket.md"):
            return "## Goal / Why\nother goal\n## Scope in / Scope out\nScope in:\nother scope\nScope out:\nexcluded\n## Verification\nsecret"
        if args == ("diff", "--cached", "reviewed", "--", "src/0"):
            return "resolution delta"
        return "ticket text" if args[0] == "show" else "wrong delta"

    async def run(stage, consumed, **kwargs):
        prompts.append((stage.surface, stage.render(None, []), kwargs))
        return replies.pop(0)

    spec = load_spec(
        "---\nllm_surface: resolve\ntier: high\neffort: high\nversion: '1.0'\n---\n"
        + "## Role\nResolve\n## Task\nResolve\n## Inputs\n"
        + "\n".join(f"{data_open(n)}\n{{{{{n}}}}}\n{data_close(n)}" for n in ("ticket", "other_tickets", "conflicts", "retry_findings"))
        + "\n## Output format\nJSON\n## On-failure\nDecline\n"
    )
    monkeypatch.setattr(stages, "_spec", lambda *args: spec)
    monkeypatch.setattr(stages, "review_stage", lambda ctx, text, diff, prior: (SimpleNamespace(surface="review", render=lambda *args: diff), spec))
    git = GitFake(_run=git_run, rev_parse="abc")
    driver = SimpleNamespace(run=run, redactor=SimpleNamespace(scrub=lambda s: s), journal=SimpleNamespace(append=lambda *args, **kwargs: signals.append(args[1])))
    config = SimpleNamespace(engine_plane_safety_inventory=[], scheduler=SimpleNamespace(parallel=SimpleNamespace(shared_paths=[])))
    ctx = SimpleNamespace(
        repo=Path("/virtual"), worktree=lambda _: Path("/virtual/work"), git=git, driver=driver, config=config, fs=SimpleNamespace(write=lambda path, data: writes.update({str(path): data}))
    )
    ticket = SimpleNamespace(stem="work", sections={"Goal / Why": "our goal", "Scope in / Scope out": "Scope in:\nour scope\nScope out:\nno"}, stuck_minutes=20, expected_minutes=10)
    return MergeQueue(ctx, escalate=lambda _: None), ticket, writes, signals, prompts


def result(artifact=None, outcome="ok"):
    return StageResult(outcome=outcome, artifact=artifact, findings=[], cost=Cost())


@pytest.mark.parametrize("mode", ["approve", "decline", "malformed", "markers", "paths", "binary", "snag", "review_invalid", "ineligible"])
def test_model_paths(monkeypatch, mode):
    reply = ResolveReply(verdict="decline" if mode == "decline" else "resolved", reason="incompatible intent", files={"src/0": "combined"})
    if mode in {"markers", "binary", "paths"}:
        reply = reply.model_copy(update={"files": {"wrong" if mode == "paths" else "src/0": "<<<<<<< left\n" if mode == "markers" else "a\0" if mode == "binary" else "combined"}})
    review = stages.ReviewVerdict(
        verdict="snag" if mode == "snag" else "approve",
        summary="reviewed",
        findings=[] if mode != "snag" else [dict(code="logic", message="bad resolution", paved_road="repair", path=None, line=None)],
    )
    replies = [result(outcome="invalid_artifact") if mode == "malformed" else result(reply), result(review, "invalid_artifact" if mode == "review_invalid" else "ok")]
    queue, ticket, writes, signals, prompts = rig(monkeypatch, replies)
    if mode == "ineligible":
        queue.ctx.config.engine_plane_safety_inventory = ["src"]
    findings = asyncio.run(queue._model_resolve(ticket, 1, ["src/0"], files(), {}, [], "reviewed", "base"))
    if mode == "ineligible":
        assert findings is None and not prompts  # Calling before the bounds would record a prompt.
    elif mode == "approve":
        assert findings == []  # Discarding an approval would hand off instead.
        assert [p[0] for p in prompts] == ["resolve", "review"]  # Approval cannot be reused.
        assert prompts[1][1] == "resolution delta"  # Reviewing the old ticket diff misses the repair.
        assert writes == {"/virtual/work/src/0": b"combined"}  # Writing ours/theirs differs.
        assert prompts[0][2]["tier"] == "high" and prompts[0][2]["effort"] == "high"
        assert "our goal" in prompts[0][1] and "other goal" in prompts[0][1] and "other scope" in prompts[0][1] and "our scope" in prompts[0][1]
        # Swapping ours and theirs would silently reverse which ticket owns each edit.
        assert '"base": "base", "ours": "main", "theirs": "ticket"' in prompts[0][1]
        assert "excluded" not in prompts[0][1] and "secret" not in prompts[0][1]  # Scope out is not intent input.
        queue._facts("work", {"src/0"}, set(), model=True)
        assert signals[0]["resolving_rung"] == "model"  # Strategies are empty, so default rung would be none.
    else:
        assert findings  # Refusals cannot be mistaken for a successful repair.
        if mode in {"decline", "malformed", "markers", "paths", "binary"}:
            assert not writes and not [call for call in queue.ctx.git.calls if call[0] == "add"]  # Validate before staging any member.
        if mode == "decline":
            assert "incompatible intent" in findings[0].message


@pytest.mark.parametrize("surface", ["resolve", "review"])
def test_merge_stage_restored_after_resolution(surface):
    from clutch.driver import Driver

    driver = Driver.__new__(Driver)
    driver._open_stage = None
    driver.log = SimpleNamespace(event=lambda *args, **kwargs: None)
    with driver.stage(stem="work", attempt=1, surface="merge"):
        with pytest.raises(RuntimeError, match="cancelled resolution"):
            with driver.stage(stem="work", attempt=1, surface=surface):
                assert driver._open_stage == ("work", surface)  # Forgetting the inner identity misattributes work.
                raise RuntimeError("cancelled resolution")
        assert driver._open_stage == ("work", "merge")  # Clearing instead of restoring loses the outer stage.
        with pytest.raises(ValueError, match="stage already open"):
            with driver.stage(stem="another", attempt=1, surface=surface):
                pass  # Allowing another ticket's review to nest breaks stage ownership.
    assert driver._open_stage is None  # Restoring merge beyond its own lifetime leaves the driver unusable.
