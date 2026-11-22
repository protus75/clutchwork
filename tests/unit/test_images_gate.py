# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: image_quality gate judges graphics render artifacts without writing files, writes side-by-side and heatmap previews, skips non-command modes, and runs after the render command in Check
# relates: [clutch/images.py, clutch/seams.py, clutch/stages.py]
# owner: engine
# verified: d80fccb7
# hash: 044f1f603f36eddf62d82b9c7f883e30d01ef5a16ea3d2a257cd2365d58e16e9
import asyncio
import json
from contextlib import nullcontext
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import Mock

import numpy as np
from PIL import Image

from clutch import images, stages
from clutch.seams import LocalFileSystem


def evidence(**updates):
    return stages.Evidence(stem="work", head_sha="abc", claimed="ok", scope_fence=[], inserted_lines=0, verification=[], run_record=None, **({"changed_files": []} | updates))


def image(path, blank=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    pixels = np.zeros((64, 64, 3), dtype=np.uint8) if blank else np.random.default_rng(37).integers(0, 256, (64, 64, 3), dtype=np.uint8)
    Image.fromarray(pixels).save(path)


def test_gate_judges_and_is_pure(tmp_path, monkeypatch):
    candidate = tmp_path / "render/out/a.png"
    image(candidate)
    item = evidence(is_graphics=True, render_dir=str(tmp_path / "render"), render={"artifact": ["out/a.png"]})
    before = sorted(tmp_path.rglob("*"))
    report = stages.ImageQualityGate().check(item, tmp_path)
    assert report.verdict == "pass" and report.findings == []
    assert sorted(tmp_path.rglob("*")) == before
    image(candidate, blank=True)
    report = stages.ImageQualityGate().check(item, tmp_path)
    assert report.verdict == "fail" and "out/a.png" in report.findings[0].message
    monkeypatch.setattr(images, "_load", Mock(side_effect=ImportError))
    report = stages.ImageQualityGate().check(item, tmp_path)
    assert report.verdict == "fail" and "clutchwork[images]" in report.findings[0].paved_road
    report = stages.ImageQualityGate().check(item.model_copy(update={"is_graphics": False}), tmp_path)
    assert report.verdict == "pass" and not report.findings
    assert sorted(tmp_path.rglob("*")) == before


def test_preview_writer(tmp_path):
    candidate = tmp_path / "render/out/a.png"
    base = tmp_path / "base.png"
    image(candidate)
    image(base)
    item = evidence(is_graphics=True, render_dir=str(tmp_path / "render"), render={"artifact": ["out/a.png"], "input": ["base.png"]})
    stages.write_image_previews(LocalFileSystem(), item, tmp_path)
    side = candidate.with_name("a.png.side-by-side.png")
    heat = candidate.with_name("a.png.heatmap.png")
    with Image.open(side) as result:
        assert result.size == (128, 64)
    with Image.open(heat) as result:
        assert result.size == (64, 64)
    assert not list(tmp_path.rglob("tickets"))
    heat.unlink()
    stages.write_image_previews(LocalFileSystem(), item.model_copy(update={"render": {"artifact": ["out/a.png"]}}), tmp_path)
    with Image.open(side) as result:
        assert result.size == (64, 64)
    assert not heat.exists()


def test_gather_stage_and_mode(tmp_path, monkeypatch):
    async def safety(*args):
        return evidence(is_graphics=True, changed_files=["changed.py"])

    monkeypatch.setattr(stages, "gather_safety_evidence", safety)
    ctx = SimpleNamespace(repo=tmp_path, worktree=lambda stem: tmp_path / "work", driver=SimpleNamespace(spool=SimpleNamespace(root=tmp_path / "spool")))
    ticket = SimpleNamespace(stem="work", verification=[], sections={"Render": "- mode: generate\n- artifact: out.png"}, frontmatter=SimpleNamespace(kind="graphics"))
    for stage, mode in [("merge", "command"), ("check", "generate")]:
        ticket.sections["Render"] = f"- mode: {mode}\n- artifact: out.png"
        item = asyncio.run(stages.gather_evidence(ctx, ticket, "already_satisfied", attempt=3, stage=stage))
        assert item.render_dir == ""
        report = stages.ImageQualityGate().check(item, tmp_path)
        assert report.verdict == "pass" and not report.findings


def test_check_runs_render_before_gate(tmp_path, monkeypatch):
    monkeypatch.setattr(stages, "child_env", lambda env, config: dict(env))
    work = tmp_path / "work"
    render = stages.render_scratch_dir(tmp_path, "work", 2)
    item = evidence(is_graphics=True, render_dir=str(render), render={"artifact": ["out.png"]})
    driver = SimpleNamespace(
        clock=lambda: datetime(2020, 1, 1, tzinfo=timezone.utc),
        spool=SimpleNamespace(root=tmp_path / "spool", write=Mock()),
        redactor=SimpleNamespace(scrub=lambda text: text),
        provider_wait=lambda *args: 0,
        stage=lambda **kwargs: nullcontext(SimpleNamespace(end=lambda outcome: None)),
    )
    ctx = SimpleNamespace(
        driver=driver, env={}, config=SimpleNamespace(state_dir=tmp_path, meta=SimpleNamespace(paths=[]), review=SimpleNamespace(autofix=[])), worktree=lambda stem: work, fs=LocalFileSystem()
    )
    ticket = SimpleNamespace(
        stem="work",
        stuck_minutes=3,
        frontmatter=SimpleNamespace(kind="graphics", gate_bypass=[]),
        sections={"Render": "```\npython tests/render.py\n```\n- mode: command\n- artifact: out.png\n- carries: tests"},
        verification=[],
    )
    state = {"fail": False}

    async def run(argv, **kwargs):
        if state["fail"]:
            return 2, '{"render_result":"error"}', ""
        image(work / "out.png")
        return 0, json.dumps({"render_result": "ok", "artifacts": ["out.png"]}), ""

    async def gather(*args, **kwargs):
        return item

    async def hosts(*args):
        return [], []

    async def lift(*args, **kwargs):
        pass

    ctx.exec_ = SimpleNamespace(run=run)
    monkeypatch.setattr(stages, "gather_evidence", gather)
    monkeypatch.setattr(stages, "check_hosts", hosts)
    monkeypatch.setattr(stages, "lift_outbox", lift)
    monkeypatch.setattr(stages, "CHECK_GATES", (stages.ImageQualityGate(),))
    monkeypatch.setattr(stages, "check_severity", lambda *args: None)
    result = asyncio.run(stages.check(ctx, ticket, SimpleNamespace(outcome="ok"), attempt=2))
    assert next(r for r in result.artifact.reports if r.code == "image_quality").verdict == "pass"
    side = render / "out.png.side-by-side.png"
    assert side.exists()
    side.unlink()
    state["fail"] = True
    (render / "out.png").unlink()
    result = asyncio.run(stages.check(ctx, ticket, SimpleNamespace(outcome="ok"), attempt=2))
    report = next(r for r in result.artifact.reports if r.code == "image_quality")
    assert report.verdict == "pass" and not report.findings
    assert not side.exists() and not list(render.rglob("*.heatmap.png"))
