import asyncio
import json
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from clutch import stages
from clutch.seams import LocalFileSystem


@pytest.mark.parametrize(
    "stdout,rc,expected",
    [
        ('{"render_result":"ok","artifacts":["a.png"]}', 0, ("ok", ["a.png"])),
        ('{"render_result":"ok","artifacts":["a.png"]}', 1, None),
        ('{"render_result":"ok","artifacts":[],"extra":1}', 0, None),
        ('{"render_result":"ok","render_result":"ok","artifacts":[]}', 0, None),
        ('{"render_result":"ok","artifacts":"a.png"}', 0, None),
        ('{"render_result":"ok","artifacts":[]} trailing', 0, None),
        ('{"render_result":"ok"}', 0, None),
        ('{"render_result":"error"}', 2, ("error", [])),
        ('{"regression_result":"pass"}', 0, None),
    ],
)
def test_protocol(stdout, rc, expected):
    assert stages.decode_render(stdout, rc) == expected


@pytest.mark.parametrize(
    "path,data,valid",
    [
        ("a.png", None, False),
        ("a.png", b"", False),
        ("a.png", b"bad", False),
        ("a.png", b"\x89PNG\r\n\x1a\ncontent", True),
        ("a.svg", b"<html/>", False),
        ("a.svg", b"<svg/>", True),
        ("a.html", b"no tag", False),
        ("a.html", b"<!doctype html><html lang='en'>", True),
        ("a.txt", b"x", True),
    ],
)
def test_content(path, data, valid):
    assert (stages.artifact_problem(path, data) is None) == valid


def setup(monkeypatch, tmp_path, paths, *, kind="graphics", mode="command", rc=0):
    monkeypatch.setattr(stages, "child_env", lambda env, config: dict(env))
    calls = []

    async def run(argv, **kwargs):
        calls.append(argv)
        return rc, json.dumps({"render_result": "ok", "artifacts": paths}), "diagnostic stderr"

    driver = SimpleNamespace(
        clock=lambda: datetime(2020, 1, 1, tzinfo=timezone.utc),
        spool=SimpleNamespace(root=tmp_path / "spool", write=Mock()),
        redactor=SimpleNamespace(scrub=lambda text: text),
        provider_wait=lambda *args: 0,
    )
    ctx = SimpleNamespace(
        driver=driver, env={}, config=SimpleNamespace(review=SimpleNamespace(autofix=[])), exec_=SimpleNamespace(run=run), worktree=lambda stem: tmp_path / "worktree", fs=LocalFileSystem()
    )
    render = "```\npython tests/render/do.py\n```\n- mode: command\n- artifact: output/a.png\n- carries: tests/render"
    if mode == "generate":
        render = "- mode: generate\n- artifact: output/a.png"
    ticket = SimpleNamespace(stem="work", stuck_minutes=3, frontmatter=SimpleNamespace(kind=kind, gate_bypass=[]), sections={"Render": render}, verification=[])
    return ctx, ticket, calls


def test_success_and_error(monkeypatch, tmp_path):
    ctx, ticket, calls = setup(monkeypatch, tmp_path, ["output/a.png"])
    data = b"\x89PNG\r\n\x1a\nactual"
    ctx.fs.write(ctx.worktree("work") / "output/a.png", data)
    reports, hard = asyncio.run(stages.check_render(ctx, ticket, 4))
    assert not hard and reports[0].verdict == "pass"
    assert (ctx.driver.spool.root / "work/4/render/output/a.png").read_bytes() == data
    assert calls == [("python", "tests/render/do.py")]


@pytest.mark.parametrize("paths", [[], ["output/a.png", "extra.png"], ["../x.png"], ["/x.png"]])
def test_bad_paths_and_sets(monkeypatch, tmp_path, paths):
    ctx, ticket, _ = setup(monkeypatch, tmp_path, paths)
    ctx.fs.read_bytes = Mock(side_effect=AssertionError("must not read"))
    reports, hard = asyncio.run(stages.check_render(ctx, ticket, 4))
    assert reports[0].verdict == "fail" and hard[0].paved_road
    assert not (ctx.driver.spool.root / "work/4/render").exists()


@pytest.mark.parametrize("kind,mode", [("feature", "command"), ("graphics", "generate")])
def test_skip(monkeypatch, tmp_path, kind, mode):
    ctx, ticket, calls = setup(monkeypatch, tmp_path, [], kind=kind, mode=mode)
    assert asyncio.run(stages.check_render(ctx, ticket, 4)) == ([], [])
    assert calls == []


def test_check_wiring(monkeypatch, tmp_path):
    ctx, ticket, _ = setup(monkeypatch, tmp_path, [])

    async def run(*args, **kwargs):
        return 2, '{"render_result":"error"}', ""

    ctx.exec_.run = run

    async def evidence(*args, **kwargs):
        return SimpleNamespace(changed_files=[], head_sha="abc", inserted_lines=0, verification=[])

    async def hosts(*args):
        return [], []

    async def lift(*args, **kwargs):
        pass

    monkeypatch.setattr(stages, "gather_evidence", evidence)
    monkeypatch.setattr(stages, "check_hosts", hosts)
    monkeypatch.setattr(stages, "lift_outbox", lift)
    monkeypatch.setattr(stages, "check_severity", lambda *args: None)
    monkeypatch.setattr(stages, "run_gates", lambda *args, **kwargs: SimpleNamespace(passed=True, reports=[], hard_failures=[], findings=[]))
    result = asyncio.run(stages.check(ctx, ticket, SimpleNamespace(outcome="ok"), attempt=1))
    assert result.outcome == "gate_failed" and any(f.code == "render" and f.paved_road for f in result.findings)
    assert any(r.code == "render" and r.verdict == "fail" for r in result.artifact.reports)
    ticket.frontmatter.kind = "feature"
    result = asyncio.run(stages.check(ctx, ticket, SimpleNamespace(outcome="ok"), attempt=1))
    assert result.outcome == "ok" and not any(f.code == "render" for f in result.findings)
    assert not any(r.code == "render" for r in result.artifact.reports)
