# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose:
# relates: [clutch/config.py, clutch/redact.py, clutch/training.py]
# owner: engine
# verified: 25fa3109
# hash: 531b5b140c6026d327899dd375be77818b428ea626d376652658656fecd0b5e9
import asyncio
import json
from pathlib import Path
from types import SimpleNamespace as NS

from clutch import training
from clutch.config import TrainingData
from clutch.redact import Redactor


class Store:
    def __init__(self):
        self.starts, self.ends, self.blobs = {}, {}, {}

    def add(self, seq, reply, day="2026-11-10", prompt="triage prompt"):
        key = f"llm/triage/{seq}/triage/1/1"
        self.starts[key] = NS(
            surface="triage",
            run_seq=str(seq),
            attempt=1,
            call=1,
            clock=NS(wall_start=day + "T23:59:59Z"),
            prompt=NS(blob=key + "p"),
            provider=NS(adapter="ClaudeAdapter"),
            engine=NS(version="v", spec="triage", spec_version="1"),
        )
        self.blobs[key + "p"] = prompt.encode()
        self.ends[key] = NS(raw=NS(stdout=key))
        self.blobs[key] = json.dumps({"type": "assistant", "message": {"content": [{"type": "text", "text": reply}]}}).encode()
        return key

    def attempts(self):
        return []

    def call_keys(self, prefix):
        return [key for key in self.starts if key.startswith(prefix)]

    def read_record(self, key, kind):
        try:
            return (self.starts if kind == "start" else self.ends)[key]
        except KeyError:
            raise FileNotFoundError(key) from None

    def get_blob(self, key):
        try:
            return self.blobs[key]
        except KeyError:
            raise FileNotFoundError(key) from None


class Git:
    async def merged_tickets(self, repo):
        return []


def export(store, **kwargs):
    return asyncio.run(training.render(store, Git(), Path("/repo"), Redactor({}), TrainingData(enabled=True), lambda path: b"", **kwargs))


def test_labels_and_records():
    store = Store()
    reply = '{"verdict":"author"}'
    for seq in (4, 2, 1, 3):
        store.add(seq, reply, prompt=f"prompt {seq}")
    messages = [NS(seq=1, status="resolved", resolution=NS(kind="declined")), NS(seq=2, status="resolved", resolution=NS(kind="ticket")), NS(seq=3, status="pending", resolution=None)]
    files, counts = export(store, kinds=("triage",), box_messages=messages)
    rows = [json.loads(line) for line in files["triage.jsonl"].splitlines()]
    assert [(r["kind"], r["stem"], r["group"], r["run_seq"], r["label"]) for r in rows] == [
        ("triage", "triage", "triage", 1, "negative"),
        ("triage", "triage", "triage", 2, "merged"),
        ("triage", "triage", "triage", 3, "neutral"),
        ("triage", "triage", "triage", 4, "neutral"),
    ]
    assert rows[0]["messages"] == [{"role": "user", "content": "prompt 1"}, {"role": "assistant", "content": reply}]
    assert counts["triage"] == 4
    assert "triage: 4" in training.report(counts)[1]
    assert export(store, kinds=("triage",), box_messages=messages)[0] == files


def test_invalid_missing_since_scrub_and_holdout():
    store = Store()
    store.add(1, '{"verdict":"author"}', day="2026-11-09")
    store.add(2, '{"verdict":"declined"}')
    store.add(3, "bad json")
    store.add(4, '{"verdict":"unknown"}')
    key = store.add(5, '{"verdict":"author"}')
    del store.ends[key]
    key = store.add(6, '{"verdict":"author"}')
    del store.blobs[key + "p"]
    store.add(7, '{"verdict":"tombstone"}', prompt="Bearer " + "x" * 20)
    files, counts = export(store, kinds=("triage",), since="2026-11-10")
    assert [json.loads(line)["run_seq"] for line in files["triage.jsonl"].splitlines()] == [2]
    assert (counts["skipped"], counts["dropped"], counts["triage"]) == (4, 1, 1)
    files, counts = export(store, kinds=("triage",), holdout=100)
    assert files["triage.jsonl"] == b"" and b"triage\n" in files["holdout.txt"] and counts["heldout"] == 1
    files, counts = export(store, kinds=("review",))
    assert "triage.jsonl" not in files and counts["triage"] == 0
