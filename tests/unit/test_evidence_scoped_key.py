"""Scoped effect keys retain their identity in evidence records."""

import asyncio
import json

from clutch.effects import Effects
from clutch.llmeffect import llm_call, scoped_seq
from clutch.redact import Redactor
from tests.unit.test_evidence_envelope import ENV, Rig


def test_scoped_key_evidence(tmp_path, monkeypatch):
    rig = Rig(tmp_path, monkeypatch)
    key = "llm/ticket/sup-3/review/2/4"
    result = asyncio.run(
        llm_call(Effects(rig.journal), rig.client, rig.request(), Redactor.from_config(rig.cfg, ENV), ticket="ticket", stem="ticket", run_seq=scoped_seq("sup", 3), attempt=2, call_seq=4)
    )
    start = rig.store.read_record(key, "start")
    end = rig.store.read_record(key, "end")
    raw = json.loads(rig.fs.read_bytes(rig.store._record_path(key, "start")))
    # Rules out a skipped provider, a changed identity or scope, swapped key fields, and a failed call.
    assert result["text"] == "answer"
    assert start.id == key
    assert start.run_seq == "sup-3"
    assert raw["run_seq"] == "sup-3"
    assert (start.group, start.surface, start.attempt, start.call) == ("ticket", "review", 2, 4)
    assert end.exit.status == "ok"
