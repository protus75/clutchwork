from pathlib import Path
from types import SimpleNamespace as NS

from clutch import observe, status
from clutch.box import Box
from clutch.observe import _shared_fences
from clutch.tickets import Frontmatter, Ticket
from tests.unit.test_menu_admission import dispatch_ticket, fake_snapshot_inputs


def ticket(stem, *paths):
    return Ticket(stem, Frontmatter(state="confirmed", source="human", priority="P1", kind="feature"), {}, (), (), (), paths, (), 1, 2)


def test_shared_paths_are_sorted_and_distinct():
    tickets = [ticket("one", "c.py", "a.py", "a.py/", "b.py"), ticket("two", "b.py", "a.py"), ticket("three", "a.py")]
    assert _shared_fences(tickets) == {
        "one": "a.py (also: three, two)\nb.py (also: two)",
        "two": "a.py (also: one, three)\nb.py (also: one)",
        "three": "a.py (also: one, two)",
    }


def test_excludes_outbox_and_unshared_paths():
    assert _shared_fences([ticket("work", "tickets/work", "tickets/work/ticket.md", "one.py"), ticket("other", "tickets/work", "two.py")]) == {}


def test_snapshot_shared_fence_details(monkeypatch):
    root = Path("/fake")
    tickets = {stem: NS(**{**vars(dispatch_ticket()), "stem": stem, "scope_fence": paths}) for stem, paths in (("one", ("shared.py",)), ("two", ("shared.py",)), ("lone", ()))}
    monkeypatch.setattr(observe, "help_payload", lambda: ({key: {"what": key, "text": key} for key in __import__("clutch.help", fromlist=["TOPICS"]).TOPICS}, []))
    monkeypatch.setattr(Box, "messages", lambda self: [])
    monkeypatch.setattr(observe, "journal", lambda *a: [])
    monkeypatch.setattr(observe, "journal_facts", lambda state, history: status.admission_facts(history))
    monkeypatch.setattr(observe, "load_tickets", lambda *a: (tickets, {}))
    monkeypatch.setattr(observe, "uncommitted_tickets", lambda *a: (set(), set()))
    monkeypatch.setattr(observe, "committed_ticket_shas", lambda *a: {s: "blob" for s in tickets})
    monkeypatch.setattr(observe, "commits", lambda *a: {})
    monkeypatch.setattr(observe, "held", lambda *a: set())
    monkeypatch.setattr(observe, "operator_holds", lambda *a: set())
    monkeypatch.setattr(observe, "running_stems", lambda *a: [])
    monkeypatch.setattr(observe, "lock_holder", lambda *a: None)
    monkeypatch.setattr(observe, "lock_display", lambda *a: ("", None))
    monkeypatch.setattr(observe, "ticket_menu_inputs", fake_snapshot_inputs)
    rows = {r["stem"]: r for r in observe.snapshot(observe.Context(root, root / "state", root / "config", None, None, None))["rows"]}
    assert [d for d in rows["one"]["detail"] if d["heading"] == "Shared fence"] == [{"heading": "Shared fence", "text": "shared.py (also: two)"}]
    assert [d for d in rows["two"]["detail"] if d["heading"] == "Shared fence"] == [{"heading": "Shared fence", "text": "shared.py (also: one)"}]
    assert not [d for d in rows["lone"]["detail"] if d["heading"] == "Shared fence"]
