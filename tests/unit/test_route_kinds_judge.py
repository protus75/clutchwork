from clutch.providers import judge_independence_finding
from tests.unit.test_route_kinds_filter import config


def test_judge_independence():
    rows = """  - {tier: medium, surface: implement, kinds: [graphics], candidates: [{provider: codex, model: image}]}
  - {tier: medium, surface: review, candidates: [{provider: codex, model: image}]}
"""
    finding = judge_independence_finding(config(rows))
    assert finding and "codex" in finding and "image" in finding
    assert judge_independence_finding(config(rows.replace("model: image}]}\n", "model: judge}]}\n", 1))) is None
    assert judge_independence_finding(config(rows.replace("kinds: [graphics], ", ""))) is None
    assert judge_independence_finding(config(rows.replace("model: image", "model: OPERATOR-SETS-THIS"))) is None
    visual = rows + "  - {tier: medium, surface: review_visual, candidates: [{provider: codex, model: judge}]}\n"
    assert judge_independence_finding(config(visual)) is None


def test_doctor_and_lint(tmp_path, monkeypatch, capsys):
    import asyncio
    from datetime import UTC, datetime
    from types import SimpleNamespace
    from unittest.mock import AsyncMock

    from clutch import doctor
    from clutch.__main__ import _lint
    from clutch.journal import Journal
    from tests.unit.test_graphics_kind import source

    rows = """  - {tier: medium, surface: implement, kinds: [graphics], candidates: [{provider: codex, model: image}]}
  - {tier: medium, surface: review, candidates: [{provider: codex, model: image}]}
"""
    cfg = config(rows)
    cfg.state_dir = tmp_path / "state"
    clock = lambda: datetime(2026, 1, 1, tzinfo=UTC)  # noqa: E731
    monkeypatch.setattr(doctor, "load_config", lambda *args, **kwargs: cfg)
    monkeypatch.setattr(doctor, "stale_core", AsyncMock(return_value=[]))
    exec_ = SimpleNamespace(run=AsyncMock(return_value=(0, "git version", "")))

    async def check():
        return await doctor.check(repo=tmp_path, config_path=None, env={}, exec_=exec_, clock=clock, sleep=asyncio.sleep, in_venv=True)

    results = asyncio.run(check())
    assert any(r.name == "judge" and not r.passed for r in results)
    cfg.routing[1].candidates[0].model = "judge"
    assert not any(r.name == "judge" for r in asyncio.run(check()))
    cfg.routing[1].candidates[0].model = "image"
    (tmp_path / "context.txt").write_text("context")
    ticket = tmp_path / "tickets/hero/ticket.md"
    ticket.parent.mkdir(parents=True)
    render = "## Render\n- mode: generate\n- artifact: assets/hero.png\n- candidates: 3"
    ticket.write_text(source(render))
    git = SimpleNamespace(git_common_dir=AsyncMock(return_value=tmp_path / ".git"), status_porcelain=AsyncMock(return_value=""), _run=AsyncMock(return_value=""))
    checkout = SimpleNamespace(repo=tmp_path, config=cfg, git=git, journal=Journal(cfg.state_dir, clock), clock=clock)
    assert asyncio.run(_lint(checkout, ["hero"])) == 1
    assert "review_visual" in capsys.readouterr().out
    ticket.write_text(source("", kind="feature"))
    assert asyncio.run(_lint(checkout, ["hero"])) == 0
