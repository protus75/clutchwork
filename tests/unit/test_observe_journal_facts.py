# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test observe journal facts
# relates: [clutch/journal.py, clutch/observe.py, clutch/status.py, tests/unit/test_admission_facts.py]
# owner: engine
# verified: 9a610809
# hash: 5d5c8f3acd02e1e6acc1aa9f1e76a46c3197ce88a004cc986fd96987ed1affbe
import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from clutch import observe, status
from clutch.journal import Journal
from tests.unit.test_admission_facts import HISTORIES


@pytest.mark.parametrize("events", [HISTORIES[i] for i in (0, 1, 2, 3, 4, 8)])
def test_journal_facts_matches_event_folds(tmp_path, events):
    if events:
        directory = tmp_path / "journal"
        directory.mkdir()
        records = [dict(v=1, type=e.type, ts="2026-08-04T12:00:00+00:00", ticket=e.ticket, key=e.key, body=e.body) for e in events]
        (directory / "000001-20260804.jsonl").write_text("".join(json.dumps(e) + "\n" for e in records))
    history = Journal(tmp_path, lambda: None).read()
    assert observe.journal_facts(tmp_path, history) == status.admission_facts(history)


def test_hold_helpers_only_check_candidates(tmp_path, monkeypatch):
    history = [SimpleNamespace(ticket="a"), SimpleNamespace(ticket="b")]
    parked = Mock(return_value="sha")
    awaiting = Mock(return_value=True)
    monkeypatch.setattr(observe, "parked_blob", parked)
    monkeypatch.setattr(observe, "awaiting_operator", awaiting)
    monkeypatch.setattr(observe, "load_config", lambda *a, **k: SimpleNamespace(caps="caps"))
    ctx = SimpleNamespace(root=tmp_path, config=tmp_path / "missing")
    assert observe.held(history, {"a": "sha", "b": "sha"}, {"a"}) == {"a"}
    parked.assert_called_once_with(history, "a")
    assert observe.operator_holds(ctx, history, {"a"}) == {"a"}
    awaiting.assert_called_once_with(history, "a", "caps")
    monkeypatch.setattr(observe, "load_config", Mock(side_effect=AssertionError("config loaded")))
    assert observe.operator_holds(ctx, history, set()) == set()
