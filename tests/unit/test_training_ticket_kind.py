# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Tests ticket-kind export: latest author call selection, authored_by from source, skipping bad or missing calls, scrubbing, holdout, Gemini streams, and the report requiring a ticket count.
# relates: [clutch/config.py, clutch/redact.py, clutch/training.py]
# owner: engine
# verified: 69d790e1
# hash: cf51f186d17fb12ac11342e4a7022aa811fff7089d0d061b0c5a5d9e23d35279
import asyncio
import json
from pathlib import Path
from types import SimpleNamespace as NS

import pytest

from clutch import training
from clutch.config import TrainingData
from clutch.redact import Redactor
from tests.git_fake import GitFake


class Store:
    def __init__(self):
        self.starts = {}
        self.ends = {}
        self.blobs = {"prompt": b"prompt"}

    def add(self, key, reply, attempt=1, adapter="ClaudeAdapter", surface="author"):
        self.starts[key] = NS(run_seq=1, attempt=attempt, call=1, surface=surface, provider=NS(adapter=adapter), prompt=NS(blob="prompt"), engine=NS(version="v", spec="author", spec_version="1"))
        self.ends[key] = NS(raw=NS(stdout=key))
        if adapter == "AntigravityAdapter":
            events = [{"event": "step_update", "step_update": {"step_type": "agent_response", "text_delta": part}} for part in reply]
        else:
            events = [{"type": "assistant", "message": {"content": [{"type": "text", "text": part}]}} for part in reply]
        self.blobs[key] = "\n".join(json.dumps(event) for event in events).encode()

    def attempts(self):
        return []

    def call_keys(self, prefix):
        return list(self.starts)

    def read_record(self, key, kind):
        return (self.starts if kind == "start" else self.ends)[key]

    def get_blob(self, key):
        return self.blobs[key]


def export(store, source="box:retro_finding", kinds=("ticket",), holdout=0, content=None):
    text = content or f"---\nsource: {source}\n---\nTicket body"

    def read(path):
        if path != Path("/repo/tickets/a-ticket/ticket.md"):
            raise FileNotFoundError(path)
        return text.encode()

    return asyncio.run(training.render(store, GitFake(), Path("/repo"), Redactor({}), TrainingData(enabled=True), read, kinds=kinds, holdout=holdout))


def reply(stem="a-ticket"):
    return json.dumps({"stem": stem, "ticket": "draft"})


def test_latest_call_and_sources():
    store = Store()
    store.add("old", [reply()], attempt=1)
    store.add("new", [reply("wrong"), reply()], attempt=2)
    files, counts = export(store)
    row = json.loads(files["ticket.jsonl"])
    assert (row["stem"], row["authored_by"], row["attempt"], row["call_keys"], row["label"]) == ("a-ticket", "author", 2, ["new"], "neutral")
    assert row["messages"] == [{"role": "user", "content": "prompt"}, {"role": "assistant", "content": "---\nsource: box:retro_finding\n---\nTicket body"}]
    assert counts["ticket"] == 1
    assert json.loads(export(store, source="human")[0]["ticket.jsonl"])["authored_by"] == "human"
    files, counts = export(store, source="seed")
    assert files["ticket.jsonl"] == b"" and counts["skipped"] == 2


def test_bad_calls_and_scrub():
    store = Store()
    store.add("bad-json", ["not json"])
    store.add("unknown", [reply()], adapter="unknown")
    store.add("missing-end", [reply()])
    del store.ends["missing-end"]
    store.add("missing-ticket", [reply("other-ticket")])
    # The store contract reports absent records as FileNotFoundError.
    store.ends = MissingDict(store.ends)
    files, counts = export(store)
    assert files["ticket.jsonl"] == b"" and counts["skipped"] == 4
    store = Store()
    store.add("secret", [reply()])
    files, counts = export(store, content="---\nsource: human\n---\nAKIA" + "A" * 16)
    assert files["ticket.jsonl"] == b"" and counts["dropped"] == 1
    assert export(store, holdout=100)[0]["ticket.jsonl"] == b""


class MissingDict(dict):
    def __missing__(self, key):
        raise FileNotFoundError(key)


def test_surfaces_and_gemini():
    store = Store()
    store.add("implement", [reply()], surface="implement")
    store.add("review", [reply()], surface="review")
    assert export(store)[0]["ticket.jsonl"] == b""
    assert "ticket.jsonl" not in export(store, kinds=("implement",))[0]
    store.add("gemini", ['{"stem": "a-ticket", ', '"ticket": "draft"}'], adapter="AntigravityAdapter")
    files, counts = export(store)
    assert json.loads(files["ticket.jsonl"])["call_keys"] == ["gemini"] and counts["skipped"] == 0


def test_report_requires_ticket():
    counts = dict(implement=0, preference=0, review=0, diagnosis=0, ticket=2, conflict=0, triage=0, dropped=0, skipped=0, heldout=0)
    assert "ticket: 2" in training.report(counts)[1]
    del counts["ticket"]
    with pytest.raises(KeyError):
        training.report(counts)
