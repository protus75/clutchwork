import pytest
from pydantic import ValidationError

from clutch.box import Box, Message
from clutch.journal import Event, EventType
from clutch.retro import RetroProposal, Window, measurements
from clutch.seams import LocalFileSystem


def window(*bodies):
    return Window("initial", tuple(Event(i, EventType.SIGNAL, "2026-01-01T00:00:00+00:00", f"t{i}", str(i), body) for i, body in enumerate(bodies, 1)), None, 1)


def fact(paths, rung="model", strategies=(), **extra):
    return {"kind": "merge_conflict_facts", "conflicted_paths": paths, "strategy_paths": strategies, "resolving_rung": rung, **extra}


def test_conflict_paths_count_per_signal_and_rung():
    w = window(fact(["a", "a", "b"], strategies=["b"]), fact(["a", "b"], strategies=["b"]), fact(["a", "c"], "rerun"))
    assert measurements(w)["conflict_paths"] == [{"path": "a", "conflicts": 3, "rungs": {"model": 2, "rerun": 1}}, {"path": "b", "conflicts": 2, "rungs": {"mechanical": 2}}]


def test_conflict_paths_cap_and_order():
    paths = [f"p{i:02}" for i in range(12)]
    rows = measurements(window(fact(paths + ["z"]), fact(paths + ["z"]), fact(["z"])))["conflict_paths"]
    assert rows == [{"path": "z", "conflicts": 3, "rungs": {"model": 3}}] + [{"path": p, "conflicts": 2, "rungs": {"model": 2}} for p in paths[:9]]


def test_conflict_paths_ignore_other_signals():
    for w in (window(), window(fact([])), window({"kind": "other", "conflicted_paths": ["a", "a2"]}, {"kind": "other", "conflicted_paths": ["a", "a2"]})):
        assert measurements(w)["conflict_paths"] == []


def test_integration_red_spike_unchanged():
    result = measurements(window(fact(["p"], integration_red_paths=["x"])))
    assert result["spikes"]["integration-red"] == 1
    assert result["conflict_paths"] == []


PROPOSAL = {"fixed_failure": "f", "overcorrection_risk": "r", "conflict_action": "split", "proposed_paths": ["clutch/big.py"]}
BASE = {
    "id": "box-1",
    "seq": 1,
    "signature": "a" * 64,
    "message_class": "retro_finding",
    "summary": "s",
    "origin": "retro",
    "stage": None,
    "outcome": None,
    "bug_origin": None,
    "has_repro": None,
    "status": "pending",
    "verdict": None,
    "resolution": None,
    "retro_report_key": "retro/1",
}
BAD = [PROPOSAL | {"proposed_paths": []}, PROPOSAL | {"test_issue": "slow"}, PROPOSAL | {"proposed_spec_paths": ["specs/review.md"]}, PROPOSAL | {"conflict_action": "merge"}]


def test_proposal_shapes_are_closed():
    assert RetroProposal.model_validate(PROPOSAL).conflict_action == "split"
    for proposal in BAD:
        with pytest.raises(ValidationError):
            RetroProposal.model_validate(proposal)


def test_message_conflict_finding_is_coherent(tmp_path):
    assert Message.model_validate(BASE | PROPOSAL).conflict_action == "split"
    for proposal in BAD:
        with pytest.raises(ValidationError):
            Message.model_validate(BASE | proposal)
    with pytest.raises(ValidationError):
        Message.model_validate(BASE | {"message_class": "suggestion", "retro_report_key": None, "conflict_action": "split"})
    box = Box(tmp_path / "box", LocalFileSystem())
    box.enqueue(
        message_class="retro_finding", origin="retro", summary="s", retro_report_key="retro/1", fixed_failure="f", overcorrection_risk="r", conflict_action="strategy", proposed_paths=["a.txt"]
    )
    assert box.messages()[0].conflict_action == "strategy"
