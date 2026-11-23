"""Check releases quarantines only for eligible passing observations."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Unit tests that Check's host-results step releases a quarantined flaky test only on a passing observation after its report was declined or its fix ticket merged, journaling one flake_released signal
# relates: [clutch/config.py, clutch/daemon.py, clutch/journal.py, clutch/stages.py, tests/git_fake.py, tests/unit/test_flake_declined_release.py]
# owner: engine
# verified: 97f3403f
# hash: fdcac8a39ee45082ed180318f7592c17a0b34b78b728d201feceb5acd2d8b064

import asyncio
import json
from datetime import UTC, datetime
from types import SimpleNamespace as NS

import pytest

from clutch import daemon, stages
from clutch.config import MechanicalCheck
from clutch.journal import EventType
from tests.git_fake import GitFake
from tests.unit.test_flake_declined_release import detect, resolve, rig


@pytest.mark.parametrize(
    ("resolution", "merged", "observation", "released"),
    [
        ("declined", False, "passed", True),
        ("declined", False, "skipped", False),
        ("declined", False, None, False),
        ("declined", False, "failed", False),
        ("ticket", False, "passed", False),
        ("ticket", True, "passed", True),
        ("tombstone", False, "passed", False),
        (None, False, "passed", False),
    ],
)
def test_check_release(tmp_path, monkeypatch, resolution, merged, observation, released):
    flake, journal, box, _ = rig()
    test = "tests/test_a.py::test_x"
    identity = next(iter(detect(flake, test).active.values()))
    if resolution:
        resolve(box, identity.box_id, resolution)
    if merged:
        journal.append(EventType.STATE_TRANSITION, {"to": "merged"}, ticket="fix-ticket")
    before = journal.read()
    monkeypatch.setattr(daemon, "storm_producer_for_config", lambda *args, **kwargs: box)
    monkeypatch.setattr(daemon, "flake_detection", lambda **kwargs: flake)

    async def execute(argv, **kwargs):
        outcomes = {test: observation} if observation else {"tests/other.py::test_y": "passed"}
        (tmp_path / "results.json").write_text(json.dumps({"schema_version": 2, "tests": outcomes, "seconds": dict.fromkeys(outcomes, 0.1)}))
        return (1 if observation == "failed" else 0), "", ""

    ctx = NS(
        worktree=lambda stem: tmp_path,
        repo=tmp_path,
        git=GitFake(),
        fs=NS(remove=lambda path: path.unlink(missing_ok=True), write=lambda path, data: path.write_bytes(data)),
        config=NS(providers=[]),
        env={},
        exec_=NS(run=execute),
        driver=NS(clock=lambda: datetime(2026, 1, 2, tzinfo=UTC), spool=NS(write=lambda *args: None), redactor=NS(scrub=lambda value: value), journal=journal),
    )
    entry = MechanicalCheck(code="tests", argv=["test"], trigger="always", severity="hard", results="results.json")
    asyncio.run(stages._check_host_results(ctx, NS(stem="ticket", stuck_minutes=1), entry, 2, 1, []))
    assert flake.quarantine().tests == (set() if released else {test})
    if released:
        event = journal.read()[-1]
        fix = f"declined:{identity.box_id}" if resolution == "declined" else "fix-ticket"
        assert event.type == EventType.SIGNAL
        assert event.key == f"flake-release/{identity.box_id}/{fix}"
        assert event.body == {"kind": "flake_released", "test_id": test, "signature": identity.signature, "box_id": identity.box_id, "fix_stem": fix}
        assert len(journal.read()) == len(before) + 1
    else:
        assert journal.read() == before
