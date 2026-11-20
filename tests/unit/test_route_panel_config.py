# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test route panel config
# relates: [clutch/config.py, clutch/doctor.py, clutch/providers.py, tests/unit/test_route_kinds_filter.py]
# owner: engine
# verified: 9a610809
# hash: 62eac3304ce487c9b02008065d55de98b51b5a2929497ebb3ee2d99282967a0f
import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from clutch import doctor
from clutch.config import ConfigError, snapshot_config
from clutch.providers import panel_members, panel_slots_finding, resolve
from tests.unit.test_route_kinds_filter import config


def row(surface="review", panel="{size: 2, combine: findings-union}", candidates="[{provider: codex}, {provider: claude}]", kinds=""):
    return f"  - {{tier: medium, surface: {surface}, {kinds}candidates: {candidates}, panel: {panel}}}\n"


def test_panel_schema():
    cfg = config(row())
    assert (cfg.routing[0].panel.size, cfg.routing[0].panel.combine) == (2, "findings-union")
    assert config("  - {tier: medium, surface: review, candidates: [{provider: codex}]}\n").routing[0].panel is None
    for value in (
        "{size: 0, combine: findings-union}",
        "{size: 4, combine: findings-union}",
        "{size: 2, combine: union}",
        "{size: 2, combine: findings-union, extra: x}",
        "{size: 2}",
        "{size: true, combine: findings-union}",
    ):
        with pytest.raises(ConfigError):
            config(row(panel=value))


@pytest.mark.parametrize(
    "surface,combiner",
    [
        ("review", "findings-union"),
        ("requisition_review", "findings-union"),
        ("diagnose", "majority-verdict"),
        ("triage", "majority-verdict"),
        ("review_visual", "majority-verdict"),
        ("implement", "best-of-n"),
    ],
)
def test_surface_fit(surface, combiner):
    assert config(row(surface, f"{{size: 2, combine: {combiner}}}")).routing[0].panel.combine == combiner


@pytest.mark.parametrize("surface,combiner", [("diagnose", "findings-union"), ("review", "majority-verdict"), ("review", "best-of-n")])
def test_surface_refusal(surface, combiner):
    with pytest.raises(ConfigError) as exc:
        config(row(surface, f"{{size: 2, combine: {combiner}}}"))
    assert exc.value.key == "routing.0.panel.combine"


def test_members_and_fallback():
    cfg = config(row())
    assert [m.provider.name for m in panel_members(cfg, "medium", "review")] == ["codex", "claude"]
    assert len(panel_members(cfg, "medium", "diagnose")) == 1
    assert [m.model for m in panel_members(snapshot_config(cfg), "medium", "review")] == ["x", "y"]
    for cs in ("[{provider: codex}]", "[{provider: codex}, {provider: claude}]"):
        cfg = config(row(panel="{size: 3, combine: findings-union}", candidates=cs))
        assert [m.provider.name for m in panel_members(cfg, "medium", "review")] == ["codex"] * 3
    cfg = config("  - {tier: medium, surface: review, candidates: [{provider: claude}]}\n" + row(kinds="kinds: [bug], "))
    assert panel_members(cfg, "medium", "review", "feature") == (resolve(cfg, "medium", "review", "feature"),)
    assert [m.provider.name for m in panel_members(cfg, "medium", "review", "bug")] == ["codex", "claude"]


def test_doctor_panel(tmp_path, monkeypatch):
    cfg = config(row())
    cfg.state_dir = tmp_path / "state"
    monkeypatch.setattr(doctor, "load_config", lambda *args, **kwargs: cfg)
    monkeypatch.setattr(doctor, "stale_core", AsyncMock(return_value=[]))
    exec_ = SimpleNamespace(run=AsyncMock(return_value=(0, "git version", "")))
    clock = lambda: datetime(2026, 1, 1, tzinfo=UTC)  # noqa: E731

    def check():
        return asyncio.run(doctor.check(repo=tmp_path, config_path=None, env={}, exec_=exec_, clock=clock, sleep=asyncio.sleep, in_venv=True))

    rows = [r for r in check() if r.name == "panel"]
    assert len(rows) == 1 and not rows[0].passed and "routing.0" in rows[0].detail and "limits.concurrency" in rows[0].detail
    cfg.routing[0].candidates.pop()
    cfg.providers[1].limits.concurrency = 2
    cfg.routing.insert(0, config(row(panel="{size: 1, combine: findings-union}", candidates="[{provider: claude}]")).routing[0])
    assert "routing.1" in panel_slots_finding(cfg)
    cfg.routing.pop(0)
    cfg.routing[0].candidates.append(config(row()).routing[0].candidates[1])
    cfg.providers[1].limits.concurrency = 2
    assert not any(r.name == "panel" for r in check())
    cfg.providers[1].limits.concurrency = 1
    cfg.routing[0].panel.size = 1
    assert panel_slots_finding(cfg) is None
    assert not any(r.name == "panel" for r in check())
    cfg.routing[0].panel = None
    assert not any(r.name == "panel" for r in check())
