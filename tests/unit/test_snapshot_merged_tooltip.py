# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Tests that snapshot ticket tooltips put the commit message before the help text only for merged rows whose commit is known, and use help text alone otherwise.
# relates: [clutch/box.py, clutch/observe.py, clutch/status.py, tests/unit/test_menu_admission.py]
# owner: clutch/observe.py
# verified: 56216342
# hash: 8259f14a619eadab47b3878c0b2317bbe4d946ab6476242c62dc2da79da7a6c4
from pathlib import Path
from types import SimpleNamespace as NS

from clutch import observe, status
from clutch.box import Box
from tests.unit.test_menu_admission import dispatch_ticket, fake_snapshot_inputs


def test_ticket_tooltips_use_commit_message_only_for_merged_commit(monkeypatch):
    root = Path("/fake")
    ticket = NS(**{**vars(dispatch_ticket()), "stem": "queued"})
    events = [
        dict(v=1, type="state_transition", ts="2026-08-01T12:00:00+00:00", ticket="with-commit", key=None, body={"to": "merged", "commit": "sha"}),
        dict(v=1, type="state_transition", ts="2026-08-02T12:00:00+00:00", ticket="without-commit", key=None, body={"to": "merged", "commit": "missing"}),
    ]
    monkeypatch.setattr(observe, "help_payload", lambda: ({key: {"what": key, "text": "help for " + key} for key in __import__("clutch.help", fromlist=["TOPICS"]).TOPICS}, []))
    monkeypatch.setattr(Box, "messages", lambda self: [])
    monkeypatch.setattr(observe, "journal", lambda *a: events)
    monkeypatch.setattr(observe, "journal_facts", lambda state, history: status.admission_facts(history))
    monkeypatch.setattr(observe, "load_tickets", lambda *a: ({"queued": ticket}, {}))
    monkeypatch.setattr(observe, "uncommitted_tickets", lambda *a: (set(), set()))
    monkeypatch.setattr(observe, "committed_ticket_shas", lambda *a: {"queued": "blob"})
    monkeypatch.setattr(observe, "commits", lambda *a: {"sha": {"subject": "subject", "message": "subject\n\nbody", "short": "s", "author": "Ada", "date": "2026-08-01T12:00:00+00:00"}})
    monkeypatch.setattr(observe, "held", lambda *a: set())
    monkeypatch.setattr(observe, "operator_holds", lambda *a: set())
    monkeypatch.setattr(observe, "running_stems", lambda *a: [])
    monkeypatch.setattr(observe, "lock_holder", lambda *a: None)
    monkeypatch.setattr(observe, "lock_display", lambda *a: ("", None))
    monkeypatch.setattr(observe, "ticket_menu_inputs", fake_snapshot_inputs)
    snap = observe.snapshot(observe.Context(root, root / "state", root / "config", None, None, None))
    rows = {row["stem"]: row for row in snap["rows"]}

    assert rows["with-commit"]["tooltip"] == "subject\n\nbody\n\nhelp for status.merged"
    assert rows["without-commit"]["tooltip"] == "help for status.merged"
    assert rows["queued"]["tooltip"] == "help for status.ready"
