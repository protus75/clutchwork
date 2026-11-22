# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Checks that the snapshot attaches provider session ids from unfinished evidence call records to Recent Steps entries and ticket rows, and turns the Copy Session menu item on only when a session exists.
# relates: [clutch/box.py, clutch/help.py, clutch/observe.py, clutch/status.py, tests/unit/test_menu_admission.py]
# owner: clutch/observe.py
# verified: 778fd8bc
# hash: ee3c8ba65849f7c856fcf24c1e8faaa9e53b53af0842e74efe3db6890bef614b
import json
from types import SimpleNamespace as NS
from urllib.parse import quote

from clutch import observe, status
from clutch.box import Box
from clutch.help import TOPICS
from tests.config_fixture import build_config
from tests.unit.test_menu_admission import dispatch_ticket, fake_snapshot_inputs


def record(evidence, stem, call, ids, *, surface="implement", attempt=2, run_seq=3, ended=False):
    directory = evidence / "calls" / quote(f"llm/{stem}/{run_seq}/{surface}/{attempt}/{call}", safe="")
    directory.mkdir(parents=True)
    data = {"stem": stem, "surface": surface, "attempt": attempt, "run_seq": run_seq, "provider": {"name": "codex"}, "native_ids": ids, "clock": {"wall_start": f"2026-01-01T00:00:0{call}+00:00"}}
    (directory / "start.json").write_text(json.dumps(data))
    if ended:
        (directory / "end.json").write_text("{}")


def test_snapshot_sessions(tmp_path, monkeypatch):
    (tmp_path / "config").write_text(build_config())
    state = tmp_path / "state"
    evidence = state / "evidence"
    record(evidence, "active", 1, {"thread_id": "t1"})
    record(evidence, "active", 2, {"session_id": "s1"}, surface="review")
    record(evidence, "finished", 1, {"session_id": "closed"}, ended=True)
    record(evidence, "stale", 1, {"thread_id": "old"})
    record(evidence, "stale", 2, None)
    tickets = {stem: NS(**{**vars(dispatch_ticket()), "stem": stem}) for stem in ("active", "finished", "stale", "missing")}
    log = [{"event": "stage_start", "ts": "2026-01-01T00:00:00+00:00", "stem": stem, "surface": "implement", "attempt": 2, "run_seq": 3} for stem in tickets]
    monkeypatch.setattr(observe, "help_payload", lambda: ({key: {"what": key, "text": key} for key in TOPICS}, []))
    monkeypatch.setattr(Box, "messages", lambda self: [])
    monkeypatch.setattr(observe, "journal", lambda *a: [{"type": "state_transition", "ticket": stem, "body": {"to": "running"}, "ts": "2026-01-01T00:00:00+00:00"} for stem in ("active", "finished")])
    monkeypatch.setattr(observe, "journal_facts", lambda state, history: status.admission_facts(history))
    monkeypatch.setattr(observe, "load_tickets", lambda *a: (tickets, {}))
    monkeypatch.setattr(observe, "uncommitted_tickets", lambda *a: (set(), set()))
    monkeypatch.setattr(observe, "committed_ticket_shas", lambda *a: {})
    monkeypatch.setattr(observe, "commits", lambda *a: {})
    monkeypatch.setattr(observe, "held", lambda *a: set())
    monkeypatch.setattr(observe, "operator_holds", lambda *a: set())
    monkeypatch.setattr(observe, "running_stems", lambda *a: ["active", "finished"])
    monkeypatch.setattr(observe, "lock_holder", lambda *a: None)
    monkeypatch.setattr(observe, "lock_display", lambda *a: ("", None))
    monkeypatch.setattr(observe, "ticket_menu_inputs", fake_snapshot_inputs)
    recent_steps = observe.recent_steps
    monkeypatch.setattr(observe, "recent_steps", lambda *a: recent_steps(state, log, 20))
    snap = observe.snapshot(observe.Context(tmp_path, state, tmp_path / "config", None, None, None))
    steps = {step["stem"]: step for step in snap["steps"]}
    assert steps["active"]["session"] == {"provider": "codex", "id": "t1"}
    assert steps["active"]["contextValue"] == "session"
    for stem in ("stale", "missing"):
        assert "session" not in steps[stem] and "contextValue" not in steps[stem]
    rows = {row["stem"]: row for row in snap["rows"]}
    assert rows["active"]["sessionId"] == "s1"
    assert rows["active"]["menu"]["clutchCopySession"] == "on"
    assert "sessionId" not in rows["finished"]
    assert rows["finished"]["menu"]["clutchCopySession"] == "off"
