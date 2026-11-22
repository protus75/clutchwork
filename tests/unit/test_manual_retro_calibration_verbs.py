"""Explicit engine verbs run even when their overdue thresholds are unmet."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Unit tests that the engine retro and engine calibrate verbs run and journal below their overdue thresholds, that their help mentions manual invocation, and that all retro and calibration config fields load
# relates: [clutch/__main__.py, clutch/config.py, clutch/effects.py, clutch/journal.py, clutch/retro.py, clutch/runner.py, tests/config_fixture.py]
# owner: engine
# verified: 45e4e081
# hash: a26fe474387c310b36fecb6308508000ff2745f3ebff51aa5bde3e590e91415f

from contextlib import asynccontextmanager
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from clutch import __main__ as cli
from clutch import retro, runner
from clutch.effects import Effects
from clutch.journal import EventType
from clutch.runner import Checkout
from tests.fakes import FakeClock, FakeFileSystem
from tests.git_fake import GitFake
from tests.unit.test_status_overdue import history, settings


def test_calibrate_verb_below_threshold(monkeypatch, capsys):
    config = settings()
    config.state_dir = Path("/state")
    journal = history()
    key = "llm/manual/1/implement/1/1"
    journal.append(EventType.EFFECT_INTENT, {}, key=key)
    journal.clock.advance(180)
    journal.append(EventType.EFFECT_COMPLETION, {"cost": {"provider": "manual-provider", "model": "manual-model"}}, key=key)
    fs = FakeFileSystem()
    fs.write(Path("/repo/tickets/manual/ticket.md"), b"- expected: 12m\n")
    monkeypatch.setattr(cli, "load_config", lambda *a, **kw: config)
    monkeypatch.setattr(cli, "child_env", lambda *a: {})
    monkeypatch.setattr(cli, "Journal", lambda *a: journal)
    monkeypatch.setattr(cli, "LocalFileSystem", lambda: fs)
    # Wrong: refuse to calibrate until the threshold is met.
    assert cli.main(["engine", "calibrate"], cwd=Path("/repo"), env={}, clock=journal.clock) == 0
    # Wrong: return without printing the actual per-provider table.
    assert capsys.readouterr().out == "manual-provider/manual-model: 1 runs, estimate p50 12.0m, actual p50 3.0m, actual p90 3.0m\n"
    # Wrong: print only, journal twice or omit the configured window.
    assert [e.body for e in journal.read() if e.type == EventType.SIGNAL] == [
        {
            "signal": "estimate_calibration",
            "window": 100,
            "rows": [{"provider": "manual-provider", "model": "manual-model", "runs": 1, "expected_p50": 12.0, "actual_p50": 3.0, "actual_p90": 3.0}],
        }
    ]


@pytest.mark.asyncio
async def test_retro_verb_forces_report_below_threshold(monkeypatch, capsys):
    config = settings()
    config.state_dir = Path("/state")
    journal = history(merges=1)
    fs = FakeFileSystem()
    git = GitFake(describe="fixture", rev_parse="head", commit="manual-report", _run="operator receipt")
    checkout = Checkout(repo=Path("/repo"), config=config, env={}, exec_=None, git=git, journal=journal, fs=fs, clock=FakeClock())
    control = SimpleNamespace(providers=SimpleNamespace(close=AsyncMock()))
    driver = SimpleNamespace(
        effects=Effects(journal),
        spool=SimpleNamespace(_fs=fs),
        redactor=SimpleNamespace(scrub=lambda text: text),
        run=AsyncMock(return_value=SimpleNamespace(outcome="ok", artifact=retro.RetroArtifact(proposals=[]))),
    )
    pipeline = SimpleNamespace(stages=SimpleNamespace(driver=driver))

    @asynccontextmanager
    async def locked(*a, **kw):
        yield

    monkeypatch.setattr(cli, "_locked", locked)
    monkeypatch.setattr(cli, "build_control", lambda c: control)
    monkeypatch.setattr(runner, "reap", AsyncMock())
    monkeypatch.setattr(runner, "call_timeout", lambda c: 30)
    # The spec/file and provider seams stay in memory; report commit uses real effects.
    monkeypatch.setattr(runner, "SPECS_DIR", Path("/specs"))
    monkeypatch.setattr(Path, "read_text", lambda *a, **kw: "spec fixture")
    monkeypatch.setattr(retro, "load_spec", lambda text: SimpleNamespace(meta=SimpleNamespace(version=1, tier="medium", effort="medium")))
    monkeypatch.setattr(retro, "production_evidence", AsyncMock(return_value={}))
    monkeypatch.setattr(retro.Retro, "tombstones", lambda self: [])
    monkeypatch.setattr(retro, "render_report", lambda *a: "manual report\n")
    monkeypatch.setattr("clutch.daemon.storm_producer_for_config", lambda *a, **kw: SimpleNamespace(messages=lambda: []))
    # Wrong: apply automatic due thresholds to the manual verb.
    assert await cli._retro(checkout, lambda c: pipeline) == 0
    # Wrong: report success without committing through the report effect.
    assert [(args, kwargs) for name, args, kwargs in git.calls if name == "commit"] == [
        ((Path("/repo"), "clutch: retro 000001"), {"only": ["tickets/retro/000001.md"]}),
    ]
    assert fs.read_bytes(Path("/repo/tickets/retro/000001.md")) == b"manual report\n"
    assert [(e.key, e.body) for e in journal.read() if e.type == EventType.EFFECT_COMPLETION] == [("retro/1", {"result": {"commit": "manual-report"}})]
    assert capsys.readouterr().out == "retro: committed tickets/retro/000001.md\n"


@pytest.mark.parametrize("command", [["engine", "retro"], ["engine", "calibrate"], ["view", "status"], ["host", "doctor"]])
def test_manual_maintenance_help(command, capsys):
    # Wrong: retain help claiming automatic runs or omit overdue discovery.
    assert cli.main(["help", *command]) == 0
    output = capsys.readouterr().out
    assert "only when invoked" in output and "overdue" in output


def test_config_loads_all_maintenance_fields():
    import yaml

    from clutch.config import Config
    from tests.config_fixture import build_config

    values = yaml.safe_load(build_config())
    values["retro"] = {
        "enabled": False,
        "test_timing": False,
        "coverage": False,
        "merges": {"enabled": False, "every": 7},
        "settled": {"enabled": True, "every": 8},
        "spikes": {"enabled": True, "count": 9, "kinds": ["gate-failure"]},
    }
    values["calibration"] = {"every": 11}
    config = Config.model_validate(values, context={"base": Path("/repo")})
    # Wrong: ignore a configured field and retain its default.
    assert config.retro.model_dump() == values["retro"]
    assert config.calibration.every == 11
