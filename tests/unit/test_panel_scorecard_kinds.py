"""Panel scorecard signal pairing and agreement rows."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Tests that the panel scorecard pairs panel_facts signals with review calls and reports agreement rows split by models and samples, ignoring invalid or unmatched signals
# relates: [clutch/journal.py, clutch/retro.py, clutch/scorecard.py, tests/fakes.py, tests/unit/test_panel_scorecard.py]
# owner: engine
# verified: 06deb66c
# hash: c8f2fae78511c25ef7b77c118a549e1b29803dd383e36fe7b9876ec54b5345cf

import pytest

from clutch import scorecard
from clutch.journal import EventType
from clutch.retro import project_window
from clutch.scorecard import PanelKindRow, panel_lines, project_scorecard
from tests.fakes import FakeJournal
from tests.unit.test_panel_scorecard import call, finding, merge, worked


def signal(attempt=0, kind="models", members=None, *, stem="a", surface="review"):
    journal = FakeJournal()
    journal.append(
        EventType.SIGNAL,
        {
            "signal": "panel_facts",
            "surface": surface,
            "attempt": attempt,
            "agreement_kind": kind,
            "members": members if members is not None else [{"provider": "codex", "model": "a", "verdict": "approve"}, {"provider": "claude", "model": "b", "verdict": "snag"}],
        },
        ticket=stem,
    )
    return journal.events[0]


def test_worked_and_unsignaled():
    events = worked()
    old = project_scorecard(project_window(events))
    assert old.panel.kinds == ()
    assert panel_lines(old) == [
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
    card = project_scorecard(project_window(events[:2] + [signal()] + events[2:4] + [signal(1, "samples")] + events[4:]))
    assert card.panel.slots == old.panel.slots
    assert card.panel.kinds == (PanelKindRow("models", 1, 1, 1), PanelKindRow("samples", 1, 0, 0))
    assert panel_lines(card)[-5:] == ["", "| Agreement | Reviews | Agreed findings | Unique catches |", "| --- | ---: | ---: | ---: |", "| models | 1 | 1 | 1 |", "| samples | 1 | 0 | 0 |"]


@pytest.mark.parametrize("event", [signal(members=[]), signal(members=[{}, {}]), signal(kind="other"), signal(attempt="0"), signal(stem="other"), signal(attempt=1), signal(surface="diagnose")])
def test_invalid_or_unmatched(event):
    card = project_scorecard(project_window([call(0, 0, 0), call(1, 0, 0), event, merge()]))
    assert card.panel.kinds == ()


def test_present_slots_and_pairing(monkeypatch):
    seen = []
    original = scorecard.findings_union

    def capture(replies, members):
        seen.append([(m.provider, m.model) for m in members])
        return original(replies, members)

    monkeypatch.setattr(scorecard, "findings_union", capture)
    events = [call(1, 0, 0), call(2, 0, 0, [finding("b.py", 9)]), signal(), merge()]
    card = project_scorecard(project_window(events))
    assert seen == [[("codex", "a"), ("claude", "b")]]
    assert [(r.slot, r.unique_catches) for r in card.panel.slots] == [(1, 0), (2, 1)]
    assert card.panel.kinds == (PanelKindRow("models", 1, 0, 1),)


def test_latest_signal_and_next_run_boundary():
    from dataclasses import replace

    first = [call(0, 0, 0), call(1, 0, 0)]
    second = [replace(call(0, 0, 0), key="llm/a/m0-1/review/0/0"), replace(call(1, 0, 0), key="llm/a/m1-1/review/0/0")]
    card = project_scorecard(project_window(first + [signal(kind="samples"), signal(kind="models")] + second + [signal(kind="samples"), merge()]))
    assert card.panel.kinds == (PanelKindRow("models", 1, 0, 0), PanelKindRow("samples", 1, 0, 0))
    card = project_scorecard(project_window(first + second + [signal(kind="samples"), merge()]))
    assert card.panel.kinds == (PanelKindRow("samples", 1, 0, 0),)
