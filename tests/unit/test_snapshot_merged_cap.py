from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import Mock

from clutch import observe, status
from clutch.box import Box
from tests.unit.test_menu_admission import dispatch_ticket, fake_snapshot_inputs


def test_cap_limits_rows_and_menu_inputs(monkeypatch):
    root = Path("/fake")
    tickets = {s: NS(**{**vars(dispatch_ticket(depends=("merged-0",) if s == "open-0" else ())), "stem": s}) for s in ("open-0", "open-1")}
    events = [dict(v=1, type="state_transition", ts=f"2026-08-0{i + 1}T12:00:00+00:00", ticket=f"merged-{i}", key=None, body={"to": "merged", "commit": f"sha-{i}"}) for i in range(5)]
    monkeypatch.setattr(observe, "help_payload", lambda: ({key: {"what": key, "text": key} for key in __import__("clutch.help", fromlist=["TOPICS"]).TOPICS}, []))
    monkeypatch.setattr(Box, "messages", lambda self: [])
    monkeypatch.setattr(observe, "journal", lambda *a: events)
    monkeypatch.setattr(observe, "journal_facts", lambda state, history: status.admission_facts(history))
    monkeypatch.setattr(observe, "load_tickets", lambda *a: (tickets, {}))
    monkeypatch.setattr(observe, "uncommitted_tickets", lambda *a: (set(), set()))
    monkeypatch.setattr(observe, "committed_ticket_shas", lambda *a: {s: "blob" for s in tickets})
    monkeypatch.setattr(observe, "commits", lambda *a: {f"sha-{i}": {"subject": str(i), "short": str(i), "author": "a", "date": "2026-08-01T12:00:00+00:00"} for i in range(5)})
    monkeypatch.setattr(observe, "held", lambda *a: set())
    monkeypatch.setattr(observe, "operator_holds", lambda *a: set())
    monkeypatch.setattr(observe, "running_stems", lambda *a: [])
    monkeypatch.setattr(observe, "lock_holder", lambda *a: None)
    monkeypatch.setattr(observe, "lock_display", lambda *a: ("", None))
    spy = Mock(side_effect=fake_snapshot_inputs)
    monkeypatch.setattr(observe, "ticket_menu_inputs", spy)
    ctx = observe.Context(root, root / "state", root / "config", None, None, None)
    full = observe.snapshot(ctx)
    capped = observe.snapshot(ctx, merged_limit=2)
    full_rows = {r["stem"]: r for r in full["rows"]}
    cap_rows = {r["stem"]: r for r in capped["rows"]}
    assert [r["stem"] for r in full["rows"] if r["section"] == "merged"] == ["merged-4", "merged-3", "merged-2", "merged-1", "merged-0"]
    assert [r["stem"] for r in capped["rows"] if r["section"] == "merged"] == ["merged-4", "merged-3"]
    assert capped["counts"]["merged"] == 2
    assert spy.call_args.args[2] == {"open-0", "open-1", "merged-4", "merged-3"}
    assert full_rows["open-0"]["depends"] == ["merged-0"]
    assert cap_rows["open-0"]["depends"] == []
    for stem in tickets:
        assert {k: v for k, v in cap_rows[stem].items() if k not in ("depends", "detail", "graph")} == {k: v for k, v in full_rows[stem].items() if k not in ("depends", "detail", "graph")}
