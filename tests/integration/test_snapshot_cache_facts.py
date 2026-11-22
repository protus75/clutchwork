# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Tests that the observe snapshot opens the journal cache once, checks only candidate tickets for holds, and matches the full-history reference.
# relates: [clutch/git.py, clutch/observe.py, clutch/seams.py, clutch/status.py, tests/integration/test_config.py, tests/integration/test_drain.py]
# owner: engine
# verified: d32c32ad
# hash: b8a27a7891b4f9ccf2c5fb9473789593922e6efd4adf6be3d4f631894538c8f3
import json
import os
from datetime import datetime
from unittest.mock import Mock

import pytest

from clutch import observe, status
from clutch.git import Git, blob_sha
from clutch.seams import SubprocessExec
from tests.integration.test_config import VALID
from tests.integration.test_drain import confirmed
from tests.snapshot_scale_fixture import git

pytestmark = pytest.mark.disk_io_skip


def test_snapshot_matches_event_reference_and_checks_candidates(tmp_path, monkeypatch):
    git(tmp_path, "init", "-q", "-b", "main")
    git(tmp_path, "config", "user.name", "Fixture")
    git(tmp_path, "config", "user.email", "fixture@example.com")
    (tmp_path / "config.yaml").write_text(VALID)
    (tmp_path / "clutch").mkdir()
    (tmp_path / "clutch/thing.py").write_text("")
    (tmp_path / ".gitignore").write_text(".clutch/\n")
    stems = ["merged", "park", "changed", "spent", "orphan", "waiting", "draft", "parent", "left", "right", "dependent"]
    for stem in stems:
        path = tmp_path / "tickets" / stem / "ticket.md"
        path.parent.mkdir(parents=True)
        deps = "- draft" if stem == "waiting" else "- parent" if stem == "dependent" else "none"
        text = confirmed(depends=deps)
        if stem == "draft":
            text = text.replace("state: confirmed", "state: draft")
        path.write_text(text)
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-qm", "tickets")
    sha = git(tmp_path, "rev-parse", "HEAD")
    blob = blob_sha((tmp_path / "tickets/park/ticket.md").read_bytes())
    events = []

    def add(stem, body, kind="state_transition"):
        events.append(dict(v=1, type=kind, ts="2026-08-04T12:00:00+00:00", ticket=stem, key=None, body=body))

    add("merged", {"to": "merged", "commit": sha})
    add("park", {"to": "running", "ticket_sha": blob})
    add("park", {"to": "premise_failed"})
    add("changed", {"to": "gate_failed", "routed": "reject_queue", "reason": "ticket_changed"})
    for _ in range(3):
        add("spent", {"cap": "retry"}, "cap_consumed")
    add("spent", {"to": "gate_failed", "routed": "reject_queue"})
    add("orphan", {"to": "running"})
    add("parent", {"signal": "supersedes", "successors": ["left", "right"]}, "signal")
    add("left", {"to": "merged", "commit": sha})
    add("right", {"to": "merged", "commit": sha})
    directory = tmp_path / ".clutch/journal"
    directory.mkdir(parents=True)
    (directory / "000001-20260804.jsonl").write_text("".join(json.dumps(e) + "\n" for e in events))
    exec_ = SubprocessExec()
    ctx = observe.Context(tmp_path, tmp_path / ".clutch", tmp_path / "config.yaml", exec_, Git(exec_, env=os.environ, timeout=30, commit_lock=None), os.environ)

    class FixedDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls.fromisoformat("2026-11-19T12:00:00+00:00")

    monkeypatch.setattr(observe, "datetime", FixedDateTime)
    opening = Mock(wraps=observe.open_journal_cache)
    parked = Mock(wraps=observe.parked_blob)
    awaiting = Mock(wraps=observe.awaiting_operator)
    monkeypatch.setattr(observe, "open_journal_cache", opening)
    monkeypatch.setattr(observe, "parked_blob", parked)
    monkeypatch.setattr(observe, "awaiting_operator", awaiting)
    actual = observe.snapshot(ctx)
    assert opening.call_count == 1
    assert {call.args[1] for call in parked.call_args_list} == {"park", "changed", "spent"}
    assert parked.call_count == 3
    assert {call.args[1] for call in awaiting.call_args_list} == {"changed", "spent"}
    assert awaiting.call_count == 2
    keys = {row["stem"]: row["help"]["status"] for row in actual["rows"]}
    assert keys["merged"] == "status.merged"
    assert keys["park"] == "status.held_change"
    assert keys["changed"] == keys["spent"] == "status.held_operator"
    assert keys["orphan"] == "status.interrupted"
    assert keys["waiting"] == "status.waits_on"
    assert keys["draft"] == "status.draft"
    assert keys["dependent"] == "status.ready"
    original_held = observe.held
    original_operator = observe.operator_holds
    monkeypatch.setattr(observe, "journal_facts", lambda state, history: status.admission_facts(history))
    monkeypatch.setattr(observe, "held", lambda history, blobs, candidates: original_held(history, blobs, {e.ticket for e in history if e.ticket}))
    monkeypatch.setattr(observe, "operator_holds", lambda ctx, history, candidates: original_operator(ctx, history, {e.ticket for e in history if e.ticket}))
    assert json.loads(json.dumps(actual)) == json.loads(json.dumps(observe.snapshot(ctx)))
