"""Panel scorecard projection and rendering."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Verify journal panel attribution and scorecard rendering.
# relates: [clutch/journal.py, clutch/retro.py, clutch/scorecard.py, clutch/status.py]
# owner: engine
# verified: fc08bb14
# hash: 635d7c8e32a9e07a5b2140f586ecabacc2e217a2ec40c638975c42c544b590c3

import json

from clutch.journal import Event, EventType
from clutch.retro import RetroArtifact, measurements, project_window, render_report
from clutch.scorecard import PANEL_OUTCOMES, panel_lines, project_scorecard
from clutch.status import Status, render


def call(slot, attempt, seq, findings=(), *, cost=1.0, stem="a", text=None):
    verdict = {"verdict": "snag" if findings else "approve", "summary": "review", "findings": list(findings)}
    body = {"result": {"text": json.dumps(verdict) if text is None else text, "provider": " ", "model": " "}}
    if cost is not None:
        body["cost"] = {"usd": cost}
    return Event(1, EventType.EFFECT_COMPLETION, "2026-01-01T00:00:00+00:00", stem, f"llm/{stem}/m{slot}-0/review/{attempt}/{seq}", body)


def finding(path, line):
    return {"code": "logic", "path": path, "line": line, "message": "problem", "paved_road": "fix it"}


def merge():
    return Event(1, EventType.STATE_TRANSITION, "2026-01-01T00:00:01+00:00", "a", None, {"to": "merged"})


def worked():
    shared, unique = finding("a.py", 3), finding("b.py", 9)
    return [call(1, 0, 0, [shared, unique], cost=0.5), call(0, 0, 0, [shared]), call(0, 1, 0), call(1, 1, 0, cost=0.5), merge()]


def test_worked_and_rendering(monkeypatch):
    window = project_window(worked())
    card = project_scorecard(window)
    assert PANEL_OUTCOMES == ("no_panel_reviews", "no_cost_data", "measured")
    assert card.panel.outcome == "measured" and card.panel.panel_reviews == 2
    assert [(r.slot, r.reviews, r.unique_catches, r.unique_per_100) for r in card.panel.slots] == [(0, 2, 0, 0.0), (1, 2, 1, 50.0)]
    assert card.panel.cost_multiplier == 1.5
    lines = [
        "",
        "## Panel scorecard",
        "",
        "Panel reviews: 2; cost multiplier: 1.50",
        "",
        "| Slot | Reviews | Unique catches | Unique catches per 100 reviews |",
        "| ---: | ---: | ---: | ---: |",
        "| 0 | 2 | 0 | 0.00 |",
        "| 1 | 2 | 1 | 50.00 |",
    ]
    assert panel_lines(card) == lines
    status = Status(merged=(), in_flight=(), blocked=(), intake=(), spend_usd=0.0, scorecard=card)
    assert render(status).endswith("\n".join(lines) + "\n")
    assert render_report(window, measurements(window), {}, [], RetroArtifact(proposals=[])).endswith("\n".join(lines) + "\n")
    empty = project_window([call(0, 0, 0)])
    empty_card = project_scorecard(empty)
    empty_status = Status(merged=(), in_flight=(), blocked=(), intake=(), spend_usd=0.0, scorecard=empty_card)
    report = render_report(empty, measurements(empty), {}, [], RetroArtifact(proposals=[]))
    status_text = render(empty_status)
    monkeypatch.setattr("clutch.scorecard.panel_lines", lambda card: [])
    monkeypatch.setattr("clutch.status.panel_lines", lambda card: [])
    assert report == render_report(empty, measurements(empty), {}, [], RetroArtifact(proposals=[]))
    assert status_text == render(empty_status)
    assert report.endswith("| review | 1 | 0 | 0 | 0 | 0.0000 | 0.0000 | false |\n")
    assert status_text.endswith("| review | 1 | 0 | 0 | 0 | 0.0000 | 0.0000 | false |\n")


def test_confirmation_and_missing_slot():
    events = [call(1, 0, 0), call(2, 0, 0, [finding("b.py", 9)])]
    unmerged = project_scorecard(project_window(events)).panel
    assert [(r.slot, r.unique_catches) for r in unmerged.slots] == [(1, 0), (2, 0)]
    merged = project_scorecard(project_window(events + [merge()])).panel
    assert [(r.slot, r.unique_catches) for r in merged.slots] == [(1, 0), (2, 1)]
    before = project_scorecard(project_window([merge()] + events)).panel
    assert before.slots[1].unique_catches == 0


def test_invalid_reprompts_cost_and_empty():
    invalid = call(1, 0, 0, text="bad", cost=0.25)
    valid = call(1, 0, 1, [finding("b.py", 9)], cost=0.5)
    panel = project_scorecard(project_window([call(0, 0, 0), invalid, valid, valid, merge()])).panel
    assert panel.panel_reviews == 1 and panel.cost_multiplier == 1.75
    assert [(r.reviews, r.unique_catches) for r in panel.slots] == [(1, 0), (1, 1)]
    single = Event(1, EventType.EFFECT_COMPLETION, invalid.ts, "a", "llm/a/0/review/0/0", {"result": {"text": '{"verdict":"approve","summary":"ok","findings":[]}'}})
    for events in ([call(0, 0, 0), invalid], [single]):
        card = project_scorecard(project_window(events))
        assert card.panel.outcome == "no_panel_reviews" and card.panel.slots == () and card.panel.cost_multiplier is None
        assert panel_lines(card) == []
    card = project_scorecard(project_window([call(0, 0, 0, cost=None), call(1, 0, 0, cost=1)]))
    assert card.panel.outcome == "no_cost_data" and card.panel.cost_multiplier is None
    assert len(card.panel.slots) == 2 and "cost multiplier: n/a" in panel_lines(card)[3]


def test_invalid_shapes_and_highest_valid_sequence():
    old = call(2, 0, 0, [finding("old.py", 2)], cost=0.2)
    new = call(2, 0, 2, [finding("new.py", 3), finding("other.py", 4)], cost=0.3)
    invalid = call(2, 0, 3, text="invalid", cost=0.4)
    bad_key = Event(1, EventType.EFFECT_COMPLETION, old.ts, "a", "llm/a/m3-x/review/0/0", old.body)
    empty_ticket = Event(1, EventType.EFFECT_COMPLETION, old.ts, "", "llm/a/m4-0/review/0/0", old.body)
    card = project_scorecard(project_window([call(1, 0, 0), new, old, invalid, bad_key, empty_ticket, merge()]))
    assert [(r.slot, r.unique_catches) for r in card.panel.slots] == [(1, 0), (2, 2)]
    assert card.panel.cost_multiplier == 1.9
