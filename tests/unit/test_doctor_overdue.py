"""Doctor reuses journal-only reminders without failing setup checks."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Unit tests that host doctor shows retro and calibration overdue reminders as passing warnings only for readable history past the thresholds
# relates: [clutch/doctor.py, tests/fakes.py, tests/unit/test_status_overdue.py]
# owner: engine
# verified: 45e4e081
# hash: 89a8c606dd9c159aa13119960244f98fef3d6f098256340f4a7593f96d442c71

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from clutch import doctor
from tests.fakes import FakeClock, FakeExec
from tests.unit.test_status_overdue import history, settings


@pytest.mark.asyncio
@pytest.mark.parametrize("past,unreadable", [(True, False), (False, False), (True, True)])
async def test_doctor_warns_only_for_readable_overdue_history(monkeypatch, past, unreadable):
    config = settings()
    config.state_dir = Path("/state")
    config.evidence = SimpleNamespace(warn_gb=1)
    config.scheduler = SimpleNamespace(parallel=SimpleNamespace(enabled=False))
    journal = history(merges=25 if past else 24, calls=100 if past else 99)
    if unreadable:

        def read():
            raise ValueError("unreadable")

        journal.read = read
    monkeypatch.setattr(doctor, "load_config", lambda *a, **kw: config)
    monkeypatch.setattr(doctor, "inspect_lock", lambda *a: "available")
    monkeypatch.setattr(doctor, "Journal", lambda *a: journal)
    monkeypatch.setattr(doctor, "stale_core", AsyncMock(return_value=[]))
    monkeypatch.setattr(doctor, "size_warning", lambda *a: None)
    monkeypatch.setattr(doctor, "judge_independence_finding", lambda *a: None)
    monkeypatch.setattr(doctor, "panel_slots_finding", lambda *a: None)
    rows = await doctor.check(repo=Path("/repo"), config_path=None, env={}, exec_=FakeExec((0, "git fixture", "")), clock=FakeClock(), sleep=AsyncMock(), in_venv=True)
    warnings = [row for row in rows if row.warn]
    # Wrong: warn below threshold, warn on unreadable history, or fail overdue checks.
    assert [(row.name, row.passed) for row in warnings] == ([("retro", True), ("calibration", True)] if past and not unreadable else [])
    rendered = doctor.render(rows)
    if past and not unreadable:
        # Wrong: change WARN rendering or use details that differ from status.
        assert rendered.splitlines()[0] == "doctor: ok"
        assert [line for line in rendered.splitlines() if line.startswith("WARN")] == [
            "WARN retro: retro overdue: 25 tickets merged since the last retro; run `clutch engine retro`",
            "WARN calibration: calibration overdue: 100 Implement calls completed since the last calibration; run `clutch engine calibrate`",
        ]
    elif not unreadable:
        # Wrong: change the below-threshold output or add empty reminder rows.
        assert (
            rendered
            == "doctor: ok\nPASS venv: active Python venv\nPASS config: config schema is valid\nPASS git: git fixture\nPASS lock: available\nPASS journal: readable history (123 events)\nPASS core: routed conduct files are current\n"
        )
