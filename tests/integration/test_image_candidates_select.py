import asyncio
import json
from dataclasses import replace
from datetime import UTC, datetime

import numpy as np
import pytest
from PIL import Image

from clutch import stages
from clutch.config import load_config
from clutch.driver import Driver
from clutch.git import Git
from clutch.journal import EventType, Journal
from clutch.llm import FakeLLM
from clutch.policy import visual_identity
from clutch.seams import LocalFileSystem, SubprocessExec
from clutch.stages import PackingSlip, StageContext
from clutch.tickets import validate_ticket
from tests.integration.test_git import commit_lock
from tests.integration.test_stages import ENV, SPECS, STEM, author, git, repo  # noqa: F401


def reply(verdict, passes):
    ids = ["identity", "placement", "lighting", "unchanged", "artifacts"]
    return json.dumps({"rows": [{"id": key, "verdict": "pass" if i < passes else "fail", "observation": "observed"} for i, key in enumerate(ids)], "verdict": verdict, "reason": "observed"})


def rig(repo, replies, *, baseline=True):
    author(repo)
    base = np.random.default_rng(4).integers(0, 256, (128, 128, 3), dtype=np.uint8)
    input_path = repo / "base.png"
    Image.fromarray(base).save(input_path)
    git(repo, "add", "base.png")
    git(repo, "commit", "-m", "input")
    config_path = repo / "config.yaml"
    config_path.write_text(
        config_path.read_text().replace(
            "routing:\n", "routing:\n" + "".join(f"  - {{tier: {tier}, surface: review_visual, candidates: [{{provider: fake}}]}}\n" for tier in ("low", "medium", "high", "max"))
        )
    )
    config = load_config(None, cwd=repo)
    clock = lambda: datetime(2026, 10, 5, tzinfo=UTC)  # noqa: E731

    async def never(_):
        await asyncio.Event().wait()

    exec_ = SubprocessExec()
    driver = Driver.from_config(config, journal=Journal(config.state_dir, clock), llm=FakeLLM(replies), env=ENV, clock=clock, sleep=never)
    if baseline:
        driver.journal.append(EventType.SIGNAL, {"signal": "visual_baseline", "verdict": "GO", "identity": visual_identity(config, SPECS), "overall": 1.0, "case_count": 20})
    ctx = StageContext(
        repo=repo, config=config, env=ENV, exec_=exec_, git=Git(exec_, env=ENV, timeout=30, commit_lock=commit_lock(repo / ".clutch/state")), fs=LocalFileSystem(), driver=driver, specs_dir=SPECS
    )
    original = validate_ticket(STEM, (repo / "tickets" / STEM / "ticket.md").read_text(), repo)
    ticket = replace(
        original,
        frontmatter=original.frontmatter.model_copy(update={"kind": "graphics"}),
        sections={**original.sections, "Render": "- mode: generate\n- artifact: output.png\n- input: base.png", "Acceptance criteria": ""},
        scope_fence=("output.png",),
        verification=(("true",),),
    )
    git(repo, "worktree", "add", "-b", STEM, str(ctx.worktree(STEM)), "main")
    candidates = ctx.worktree(STEM) / ".clutch/renders" / STEM / "a0"
    candidates.mkdir(parents=True)
    for k in range(2):
        image = base.copy()
        image[25:55, 25:55] = np.random.default_rng(k + 20).integers(0, 256, (30, 30, 3), dtype=np.uint8)
        Image.fromarray(image).save(candidates / f"cand-{k}.png")
    Image.new("RGB", (128, 128), "red").save(candidates / "cand-2.png")
    record = repo / "tickets" / STEM / "run.md"
    record.write_text("".join(f"## {section}\n\n{('ok' if section == 'Outcome' else 'none')}\n\n" for section in stages.RUN_RECORD_SECTIONS))
    slip = PackingSlip(produced_by_spec_version=2, produced_at_sha=git(repo, "rev-parse", STEM).strip(), stem=STEM, branch=STEM, outcome="ok", summary="generated", run_record=str(record))
    return ctx, ticket, slip, candidates


@pytest.mark.parametrize("tie", [False, True])
def test_check_selects_or_parks(repo, tie):
    ctx, ticket, slip, candidates = rig(repo, [reply("accept", 5), reply("accept" if tie else "reject", 5 if tie else 2)])
    before = git(repo, "rev-parse", STEM).strip()

    async def run():
        with ctx.driver.stage(stem=STEM, attempt=0, surface="check"):
            return await stages.check(ctx, ticket, slip, attempt=0)

    result = asyncio.run(run())
    spool = ctx.driver.spool.root / STEM / "0/render/a0"
    assert all((spool / f"cand-{k}.png.side-by-side.png").is_file() and (spool / f"cand-{k}.png.heatmap.png").is_file() for k in (0, 1))
    if tie:
        assert [f.code for f in result.findings] == ["visual_undecided"]
        assert git(repo, "rev-parse", STEM).strip() == before
    else:
        assert result.outcome == "ok"
        assert (ctx.worktree(STEM) / "output.png").read_bytes() == (candidates / "cand-0.png").read_bytes()
        assert git(repo, "log", "-1", "--format=%s", STEM).strip() == f"clutch({STEM}): select"
        assert git(repo, "diff", "--name-only", f"main...{STEM}").split() == ["output.png"]
        assert result.artifact.changed_files == ["output.png"]
        assert next(r for r in result.artifact.reports if r.code == "verification").verdict == "pass"


def test_undecided_reoffers_then_attempts_spend(repo):
    from clutch import caps, drain, runner
    from clutch.journal import EventType

    ctx, ticket, slip, _ = rig(repo, [reply("accept", 5), reply("accept", 5)])

    async def run():
        with ctx.driver.stage(stem=STEM, attempt=0, surface="check"):
            result = await stages.check(ctx, ticket, slip, attempt=0)
        await runner.failure_terminal(ctx, ticket, outcome=result.outcome, stage="check", findings=result.findings, attempt=0)
        return result

    result = asyncio.run(run())
    assert [f.code for f in result.findings] == ["visual_undecided"]
    events = ctx.driver.journal.read()
    terminal = [e.body for e in events if e.type == EventType.STATE_TRANSITION][-1]
    assert terminal["reason"] == "visual_undecided"
    assert drain.reofferable(events, STEM, ctx.config.caps)
    drain.record_reoffer(ctx.driver.journal, events, STEM, "sha")
    assert caps.draws(ctx.driver.journal.read(), STEM, "retry") == 1
    for _ in range(ctx.config.caps.attempts - 2):
        ctx.driver.journal.append(EventType.STATE_TRANSITION, {"to": "gate_failed", "stage": "check", "reason": "visual_undecided"}, ticket=STEM)
    asyncio.run(runner.failure_terminal(ctx, ticket, outcome="gate_failed", stage="check", findings=result.findings, attempt=1))
    terminal = [e.body for e in ctx.driver.journal.read() if e.type == EventType.STATE_TRANSITION][-1]
    assert terminal["dispatch"] == "reject_queue" and terminal["routed"] == "reject_queue"
    assert not drain.reofferable(ctx.driver.journal.read(), STEM, ctx.config.caps)


def test_effect_keys_name_reprompted_winner(repo):
    ctx, ticket, slip, _ = rig(repo, ["invalid", reply("accept", 5), reply("reject", 2)])

    async def run():
        with ctx.driver.stage(stem=STEM, attempt=0, surface="check"):
            return await stages.check(ctx, ticket, slip, attempt=0)

    assert asyncio.run(run()).outcome == "ok"
    message = git(repo, "log", "-1", "--format=%B", STEM)
    assert f"llm/{STEM}/a0c0s0-0/review_visual/0/2" in message
    events = ctx.driver.journal.read()
    keys = [e.key for e in events if e.key and e.key.startswith(f"llm/{STEM}/") and e.key.endswith("/1")]
    assert any("/a0c0s0-0/" in key for key in keys)
    assert any("/a0c1s0-0/" in key for key in keys)


@pytest.mark.parametrize("forbidden", ["output.png", ".clutch/renders/other/file.png"])
def test_committed_forbidden_path_refuses(repo, forbidden):
    ctx, ticket, slip, _ = rig(repo, [])
    path = ctx.worktree(STEM) / forbidden
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"wrong")
    git(ctx.worktree(STEM), "add", "-f", forbidden)
    git(ctx.worktree(STEM), "commit", "-m", "forbidden")
    before = git(repo, "rev-parse", STEM).strip()
    findings = asyncio.run(stages.check_candidates(ctx, ticket, 0))
    assert findings[0].code == "candidate_paths" and "never an artifact path" in findings[0].paved_road
    assert git(repo, "rev-parse", STEM).strip() == before


def test_missing_visual_baseline_parks(repo):
    ctx, ticket, slip, _ = rig(repo, [], baseline=False)
    before = git(repo, "rev-parse", STEM).strip()

    async def run():
        with ctx.driver.stage(stem=STEM, attempt=0, surface="check"):
            return await stages.check(ctx, ticket, slip, attempt=0)

    result = asyncio.run(run())
    assert [f.code for f in result.findings] == ["visual_undecided"]
    assert git(repo, "rev-parse", STEM).strip() == before
    assert not (ctx.worktree(STEM) / "output.png").exists()
    assert not (ctx.driver.spool.root / STEM / "0/render").exists()
