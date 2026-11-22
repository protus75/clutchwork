# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Unit tests that snapshot rows and the queue view show the upgrade hold only while a live engine has a pending serve upgrade that has not handed off yet
# relates: [clutch/box.py, clutch/observe.py, clutch/status.py, tests/unit/test_menu_admission.py]
# owner: engine
# verified: 290c435a
# hash: bba2c39966f66149d63518cfbf8865e63b887452bbecdba082b0e08197710eb1
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace as NS

import pytest

from clutch import observe, status
from clutch.box import Box
from tests.config_fixture import build_config
from tests.unit.test_menu_admission import dispatch_ticket, fake_snapshot_inputs

START = datetime.fromisoformat("2026-08-01T12:00:00+00:00")


def signal(name, ts="2026-08-01T13:00:00+00:00"):
    return {"type": "signal", "ticket": None, "ts": ts, "body": {"signal": name}}


@pytest.mark.parametrize(
    "holder,history,expected",
    [
        (START, [signal("serve_upgrade_pending")], True),
        (START, [signal("serve_upgrade_pending", "2026-08-01T11:00:00+00:00")], False),
        (START, [signal("serve_upgrade_pending"), signal("serve_handoff")], False),
        (None, [signal("serve_upgrade_pending")], False),
    ],
)
def test_snapshot_and_queue(tmp_path, monkeypatch, holder, history, expected):
    root = tmp_path
    (root / "config").write_text(build_config())
    ticket = NS(**{**vars(dispatch_ticket()), "stem": "queued"})
    monkeypatch.setattr(observe, "help_payload", lambda: ({key: {"what": key, "text": key} for key in __import__("clutch.help", fromlist=["TOPICS"]).TOPICS}, []))
    monkeypatch.setattr(Box, "messages", lambda self: [])
    monkeypatch.setattr(observe, "journal", lambda *a: history)
    monkeypatch.setattr(observe, "journal_facts", lambda state, events: status.admission_facts(events))
    waiting = NS(**{**vars(dispatch_ticket(depends=("missing",))), "stem": "waiting"})
    held = NS(**{**vars(dispatch_ticket()), "stem": "held"})
    monkeypatch.setattr(observe, "load_tickets", lambda *a: ({"queued": ticket, "waiting": waiting, "held": held}, {}))
    monkeypatch.setattr(observe, "uncommitted_tickets", lambda *a: (set(), set()))
    monkeypatch.setattr(observe, "committed_ticket_shas", lambda *a: {"queued": "blob", "waiting": "blob", "held": "blob"})
    monkeypatch.setattr(observe, "commits", lambda *a: {})
    monkeypatch.setattr(observe, "held", lambda *a: set())
    monkeypatch.setattr(observe, "operator_holds", lambda *a: {"held"})
    monkeypatch.setattr(observe, "running_stems", lambda *a: [])
    monkeypatch.setattr(observe, "lock_holder", lambda *a: holder)
    monkeypatch.setattr(observe, "lock_display", lambda *a: ("", None))
    monkeypatch.setattr(observe, "ticket_menu_inputs", fake_snapshot_inputs)
    ctx = observe.Context(root, root / "state", root / "config", None, None, None)
    rows = {row["stem"]: row for row in observe.snapshot(ctx)["rows"]}
    assert rows["waiting"]["help"]["status"] == "status.waits_on"
    assert rows["held"]["help"]["status"] == "status.held_operator"
    row = rows["queued"]
    assert row["status"] == (observe.UPGRADE_HOLD if expected else "ready")
    assert row["help"]["status"] == ("status.upgrade_hold" if expected else "status.ready")
    monkeypatch.setattr(observe, "operator_holds", lambda *a: set())
    monkeypatch.setattr(Path, "glob", lambda *a: [root / "tickets/queued/ticket.md"])
    monkeypatch.setattr(Path, "read_text", lambda *a: (_ for _ in ()).throw(FileNotFoundError()))
    monkeypatch.setattr(observe, "frontmatter", lambda *a: {"state": "confirmed", "priority": "P1"})
    monkeypatch.setattr(observe, "depends", lambda *a: [])
    assert observe.queue(ctx, history, {}, set(), set()) == [("P1", "queued", observe.UPGRADE_HOLD if expected else "ready, not run yet")]
