from dataclasses import asdict
from pathlib import Path

import pytest

from clutch.control import _TRIAGE_SHAPE, ControlInbox, TriageRequest, decisions, validate_request
from tests.fakes import FakeClock, FakeJournal


def request(ids, lifecycle="live", name="request"):
    return TriageRequest(name, lifecycle, "triage", ids, None, "operator")


@pytest.mark.parametrize("ids", [[], ["box-000001"]])
def test_validate(ids):
    assert validate_request(asdict(request(ids)), "request.json") == request(ids)


@pytest.mark.parametrize("ids", [None, "box-000001", [1]])
def test_invalid_ids(ids):
    with pytest.raises(ValueError, match=_TRIAGE_SHAPE.replace("[", r"\[").replace("]", r"\]")):
        validate_request(asdict(request(ids)), "request.json")


def test_consume_and_fold():
    import json

    journal = FakeJournal(FakeClock())
    values = {Path("live.json"): asdict(request(["box-000001"], name="live")), Path("stale.json"): asdict(request([], "old", "stale"))}
    applied = []
    inbox = ControlInbox(journal=journal, lifecycle_id="live", holds=set, apply=applied.append, files=lambda: values, read=lambda p: json.dumps(values[p]).encode(), known=lambda _: False)
    inbox.consume()
    live, stale = [e.body for e in decisions(journal.read())]
    assert (live["decision"], live["ids"], live["actor"], live["hold_id"]) == ("accepted", ["box-000001"], "operator", None)
    assert stale["decision"] == "stale"
    projection = inbox.recover()
    assert (projection.pause_id, projection.kill_requested, projection.stop_requested, projection.retro_id) == (None, False, False, None)
    assert applied == []
