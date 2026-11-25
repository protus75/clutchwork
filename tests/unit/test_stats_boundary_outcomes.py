# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Tests the `view stats --split` boundary-outcome projection. It covers split-timestamp parsing, before/after counts for settled, premise-failed, and rework outcomes, review snags, first-pass yield, duplicate-owner review findings, and the CLI fallback to the regular stats output when no split is given.
# relates: [clutch/__main__.py, clutch/journal.py, clutch/stats.py]
# owner: engine
# verified: 5fee4e67
# hash: b7387929bddd08e21da1a710f4ff921ef67bce4fe19fb6c76d87ac9cef2ddc3c
import json
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from clutch import __main__ as entry
from clutch.journal import Event, EventType
from clutch.stats import DUPLICATE_OWNER_PATTERN, parse_split, project_split

SPLIT = datetime(2026, 1, 2, tzinfo=UTC)
NOW = datetime(2026, 1, 3, tzinfo=UTC)


def event(day, typ, body, ticket="a", key=None):
    return Event(1, typ, f"2026-01-0{day}T00:00:00+00:00", ticket, key, body)


def test_parse_split():
    assert parse_split("2026-01-02T00:00:00+00:00") == SPLIT
    for value in ("bad", "2026-01-02T00:00:00"):
        with pytest.raises(ValueError, match="bad split"):
            parse_split(value)
    with pytest.raises(ValueError, match="bad split"):
        project_split([], now=NOW, split=datetime(2026, 1, 2))


def test_projection():
    transition = EventType.STATE_TRANSITION
    events = [
        event(1, transition, {"to": "running"}),
        event(1, transition, {"to": "gate_failed", "stage": "review"}),
        event(1, transition, {"to": "merged"}),
        event(1, transition, {"to": "running"}, "b"),
        event(1, transition, {"to": "gate_failed", "stage": "review"}, "b"),
        event(2, transition, {"to": "running"}, "b"),
        event(2, transition, {"to": "merged"}, "b"),
        event(3, transition, {"to": "rejected"}, "c"),
        event(4, transition, {"to": "rejected"}, "future"),
    ]
    for stage in ("implement", "requisition", "review", "other"):
        events.append(event(2, transition, {"to": "premise_failed", "stage": stage}))
    for action in ("update", "split", "escalate"):
        events.append(event(2, EventType.SIGNAL, {"signal": "rework_order", "action": action}))
    result = project_split(events, now=NOW, split=SPLIT.isoformat())
    assert result["split"] == SPLIT.isoformat()
    assert result["before"]["settled"] == {"merged": 1, "already_satisfied": 0, "rejected": 0}
    assert result["after"]["settled"] == {"merged": 1, "already_satisfied": 0, "rejected": 1}
    assert result["after"]["premise_failed"] == {"implement": 1, "requisition": 1, "review": 1, "total": 4}
    assert result["after"]["rework"] == {"update": 1, "split": 1, "escalate": 1}
    assert result["before"]["review_snags_mean"] == 1.0
    assert result["after"]["review_snags_mean"] == 0.5
    assert result["before"]["first_pass_yield"] == 1.0
    assert result["after"]["first_pass_yield"] == 0.0
    assert project_split([], now=NOW, split=SPLIT)["before"]["first_pass_yield"] is None


def test_review_findings():
    assert DUPLICATE_OWNER_PATTERN.search("Undeclared boundaries")
    assert not DUPLICATE_OWNER_PATTERN.search("normal implementation")
    finding = {"code": "scope", "message": "duplicate owner"}
    reply = {"verdict": "snag", "findings": [finding, {"code": "acceptance", "paved_road": "canonical owner"}, {"code": "logic", "message": "duplicate owner"}, None]}
    key = "llm/a/1/review/1/1"

    def completion(text, key=key):
        return event(2, EventType.EFFECT_COMPLETION, {"result": {"text": text}}, key=key)

    events = [
        completion(json.dumps(reply)),
        completion("```json\n" + json.dumps(reply) + "\n```"),
        completion("invalid"),
        completion(json.dumps({**reply, "verdict": "approve"})),
        completion(json.dumps(reply), "llm/a/1/implement/1/1"),
        completion("[]"),
        event(2, EventType.EFFECT_COMPLETION, {"result": None}, key=key),
    ]
    assert project_split(events, now=NOW, split=SPLIT)["after"]["duplicate_owner_findings"] == 4


def test_cli_split(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(entry, "load_config", lambda *a, **kw: SimpleNamespace(state_dir=tmp_path, providers=[], snapshot_merged_limit=7, evidence=SimpleNamespace(warn_gb=20)))

    class Journal:
        def __init__(self, *args):
            pass

        def read(self):
            return []

    monkeypatch.setattr(entry, "Journal", Journal)
    for name in ("CommitLock", "SubprocessExec", "Git"):
        monkeypatch.setattr(entry, name, lambda *a, **kw: object())
    stats = AsyncMock(return_value={"legacy": 7})
    monkeypatch.setattr(entry, "_stats", stats)
    assert entry._parser().parse_args(["view", "stats", "--split", SPLIT.isoformat()]).split == SPLIT.isoformat()
    for flag in ("--json", "--tree", None):
        argv = ["view", "stats", "--split", SPLIT.isoformat()] + ([flag] if flag else [])
        assert entry.main(argv, cwd=tmp_path, env={}) == 0
        out = capsys.readouterr().out
        assert "before" in out and "after" in out
    assert stats.await_count == 0
    for value in ("bad", "2026-01-02"):
        assert entry.main(["view", "stats", "--split", value], cwd=tmp_path, env={}) == 2
        assert "bad split" in capsys.readouterr().err
    assert entry.main(["view", "stats", "--json"], cwd=tmp_path, env={}) == 0
    assert json.loads(capsys.readouterr().out) == {"legacy": 7}
    assert stats.await_count == 1
