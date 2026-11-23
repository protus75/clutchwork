"""Declined flake reports release only with matching green evidence."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Unit tests that a flake report resolved as declined is released only with matching green rerun evidence, replays idempotently, refuses a conflicting resolution, frees quarantine cap, and that ticket resolutions still require a merge.
# relates: [clutch/flake.py, clutch/journal.py]
# owner: engine
# verified: b2c11bd1
# hash: cb5934a836b7b2fb10a2c6ed646f1440c2a8be8dd89d9b6a9cdb008e1464ede0

from dataclasses import replace
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from clutch.flake import Flake, FlakeError, GreenRerunEvidence, RerunEvidence
from clutch.journal import EventType


class Journal:
    def __init__(self):
        self.events = []

    def read(self):
        return list(self.events)

    def append(self, type_, body, *, ticket=None, key=None):
        self.events.append(SimpleNamespace(type=type_, body=body, ticket=ticket, key=key, ts="2026-01-01T00:00:00+00:00"))


class Box:
    def __init__(self):
        self.messages = {}

    def enqueue(self, *, origin, **kwargs):
        box_id = str(len(self.messages) + 1)
        self.messages[box_id] = SimpleNamespace(id=box_id, signature="a" * 64, origin=origin, message_class="failure_report", stage="check", outcome="gate_failed", status="pending", resolution=None)
        return box_id, True

    def get(self, box_id):
        return self.messages[box_id]


def rig():
    journal, box, escalations = Journal(), Box(), []
    return Flake(journal=journal, box=box, cap=5, escalate=escalations.append), journal, box, escalations


def detect(flake, test_id):
    return flake.detect(test_id=test_id, evidence=RerunEvidence(test_id, "fail", "pass", True, True, True), summary="failure", reason="reason")


def resolve(box, box_id, kind="declined"):
    message = box.get(box_id)
    message.status = "resolved"
    message.resolution = SimpleNamespace(kind=kind, link="fix-ticket")


def green(test_id, box_id):
    return GreenRerunEvidence(test_id, f"declined:{box_id}", datetime(2026, 1, 1, tzinfo=UTC), "pass", True, True, True)


def test_declined_release_record_replay_and_conflict():
    flake, journal, box, _ = rig()
    identity = next(iter(detect(flake, "test-one").active.values()))
    resolve(box, identity.box_id)
    result = flake.release(box_id=identity.box_id, evidence=green(identity.test_id, identity.box_id))
    assert result.tests == set()
    assert len(journal.events) == 2
    event = journal.events[-1]
    assert (event.type, event.ticket, event.key, event.body) == (
        EventType.SIGNAL,
        None,
        f"flake-release/{identity.box_id}/declined:{identity.box_id}",
        {"kind": "flake_released", "test_id": identity.test_id, "signature": identity.signature, "box_id": identity.box_id, "fix_stem": f"declined:{identity.box_id}"},
    )
    assert flake.release(box_id=identity.box_id) == result
    assert len(journal.events) == 2
    resolve(box, identity.box_id, "ticket")
    with pytest.raises(FlakeError, match="conflicting release resolution"):
        flake.release(box_id=identity.box_id)
    assert len(journal.events) == 2


@pytest.mark.parametrize(
    "change", [None, {"result": "fail"}, {"observed": False}, {"test_id": "other"}, {"fix_stem": "other"}, {"same_workspace": False}, {"unchanged_code": False}, {"observed_at": datetime(2026, 1, 1)}]
)
def test_declined_requires_evidence(change):
    flake, journal, box, _ = rig()
    identity = next(iter(detect(flake, "test-one").active.values()))
    resolve(box, identity.box_id)
    evidence = None if change is None else replace(green(identity.test_id, identity.box_id), **change)
    before = journal.read()
    with pytest.raises(FlakeError, match="insufficient release evidence.*resolve the report"):
        flake.release(box_id=identity.box_id, evidence=evidence)
    assert journal.read() == before
    assert flake.quarantine().tests == {identity.test_id}


def test_declined_releases_free_cap():
    flake, journal, box, escalations = rig()
    identities = []
    for i in range(5):
        projection = detect(flake, f"test-{i}")
        identities.append(next(identity for identity in projection.active.values() if identity.test_id == f"test-{i}"))
    assert len(projection.tests) == 5
    for identity in identities:
        resolve(box, identity.box_id)
        flake.release(box_id=identity.box_id, evidence=green(identity.test_id, identity.box_id))
    assert detect(flake, "sixth").tests == {"sixth"}
    assert escalations == []
    assert len(journal.events) == 11


def test_ticket_still_requires_merge():
    flake, journal, box, _ = rig()
    identity = next(iter(detect(flake, "test-one").active.values()))
    resolve(box, identity.box_id, "ticket")
    before = journal.read()
    with pytest.raises(FlakeError, match="insufficient release evidence"):
        flake.release(box_id=identity.box_id, evidence=replace(green(identity.test_id, identity.box_id), fix_stem="fix-ticket"))
    assert journal.read() == before
