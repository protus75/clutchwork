# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Tests compact rendering of clutch view status --short.
# relates: [clutch/status.py, clutch/__main__.py]
# owner: clutch/status.py
# verified: 0d8da9bc
# hash: 0000000000000000000000000000000000000000000000000000000000000000
from types import MappingProxyType

from clutch.__main__ import _parser
from clutch.scorecard import Scorecard
from clutch.status import Status, render


def test_render_short_omits_resolved_box_tombstones_and_scorecard():
    status = Status(
        merged=("a",),
        in_flight=("b",),
        interrupted=(),
        blocked=(),
        intake=(),
        spend_usd=1.25,
        reject=(),
        box=(
            ("box-1", "suggestion", "pending", "open item"),
            ("box-2", "suggestion", "declined", "old item"),
        ),
        tombstones=(("box-3", "failure_report", 0),),
        reopens=(),
        verdict_refusals=(),
        verdict_decisions=(),
        scorecard=Scorecard(
            boundary="start",
            merged_ticket_count=1,
            spend_usd=1.25,
            tokens={"input": {"known": 0, "unknown_calls": 0}},
            signal_counts={},
            gate_failure_count=0,
            surfaces=(),
            panel=(),
        ),
        provenance=MappingProxyType({"at": "2026-11-24T00:00:00Z"}),
        overdue=(),
    )
    out = render(status, short=True)
    assert "box-1: suggestion: pending: open item" in out
    assert "box-2" not in out
    assert "Suggestion Box (1 pending, 1 resolved):" in out
    assert "Confirmed-class tombstones" not in out
    assert "Surface scorecard" not in out
    assert "window provenance:" in out


def test_parser_accepts_view_status_short():
    args = _parser().parse_args(["view", "status", "--short"])
    assert args.view_verb == "status"
    assert args.short is True
