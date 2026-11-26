# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Tests conflict-resolution export records: ordering, merged/neutral labels, Gemini stream assembly, skipping declined or incomplete calls, since filter, holdout, and scrubbing.
# relates: [clutch/config.py, clutch/redact.py, clutch/training.py]
# owner: engine
# verified: 69d790e1
# hash: 506c78e128e325facb3f71eb31a71929a6166e0994bdbfbca3ad601e8baa3935
import asyncio
import json
from pathlib import Path
from types import SimpleNamespace as NS

from clutch import training
from clutch.config import TrainingData
from clutch.redact import Redactor
from tests.git_fake import GitFake


class Store:
    def __init__(self):
        self.starts = {}
        self.ends = {}
        self.blobs = {}

    def add(self, stem, seq, reply, day="2026-11-10", prompt="conflict prompt", adapter="ClaudeAdapter"):
        key = f"llm/{stem}/{seq}/resolve/1/1"
        self.starts[key] = NS(
            surface="resolve",
            run_seq=seq,
            attempt=1,
            call=1,
            clock=NS(wall_start=day + "T23:59:59Z"),
            prompt=NS(blob=key + "prompt"),
            provider=NS(adapter=adapter),
            engine=NS(version="v", spec="resolve", spec_version="1"),
        )
        self.blobs[key + "prompt"] = prompt.encode()
        self.ends[key] = NS(raw=NS(stdout=key))
        parts = reply if isinstance(reply, list) else [reply]
        events = (
            [{"event": "step_update", "step_update": {"step_type": "agent_response", "text_delta": part}} for part in parts]
            if adapter == "AntigravityAdapter"
            else [{"type": "assistant", "message": {"content": [{"type": "text", "text": part}]}} for part in parts]
        )
        self.blobs[key] = "\n".join(map(json.dumps, events)).encode()
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


def export(store, **kwargs):
    return asyncio.run(training.render(store, GitFake(merged_tickets=[("sha", "merged")], diff="diff"), Path("/repo"), Redactor({}), TrainingData(enabled=True), lambda path: b"", **kwargs))


def rows(files):
    return [json.loads(line) for line in files["conflict.jsonl"].splitlines()]


def test_records_and_order():
    store = Store()
    reply = '{"verdict": "resolved", "reason": "fixed", "files": {}}'
    key = store.add("merged", "resolve2abc-1", reply)
    store.add("other", "resolve9-2", [reply[:20], reply[20:]], adapter="AntigravityAdapter")
    store.add("merged", "resolve1-1", reply, prompt="another prompt")
    files, counts = export(store, kinds=("conflict",))
    result = rows(files)
    assert [(r["stem"], r["run_seq"], r["label"]) for r in result] == [("merged", "resolve1-1", "merged"), ("merged", "resolve2abc-1", "merged"), ("other", "resolve9-2", "neutral")]
    assert result[1]["call_keys"] == [key] and result[1]["kind"] == "conflict"
    assert result[1]["messages"] == [{"role": "user", "content": "conflict prompt"}, {"role": "assistant", "content": reply}]
    assert result[2]["messages"][1]["content"] == reply
    assert counts["conflict"] == 3 and counts["skipped"] == 0
    assert export(store, kinds=("conflict",))[0] == files


def test_incomplete_and_declined_calls():
    store = Store()
    store.add("decline", "resolve1-1", '{"verdict":"decline"}')
    key = store.add("missing", "resolve1-1", '{"verdict":"resolved"}')
    del store.ends[key]
    store.add("invalid", "resolve1-1", "not json")
    key = store.add("prompt", "resolve1-1", '{"verdict":"resolved"}')
    del store.blobs[key + "prompt"]
    files, counts = export(store, kinds=("conflict",))
    assert rows(files) == [] and counts["skipped"] == 4 and counts["conflict"] == 0


def test_since_holdout_and_scrub():
    store = Store()
    store.add("old", "resolve1-1", '{"verdict":"resolved"}', day="2026-11-09")
    store.add("new", "resolve1-1", '{"verdict":"resolved"}')
    files, counts = export(store, kinds=("conflict",), since="2026-11-10")
    assert [r["stem"] for r in rows(files)] == ["new"] and counts["skipped"] == 0
    files, counts = export(store, kinds=("conflict",), holdout=100)
    assert rows(files) == [] and counts["heldout"] == 3
    store.add("secret", "resolve1-1", '{"verdict":"resolved"}', prompt="Bearer " + "x" * 20)
    files, counts = export(store, kinds=("conflict",), since="2026-11-10")
    assert [r["stem"] for r in rows(files)] == ["new"] and counts["dropped"] == 1


def test_unrequested_and_report():
    store = Store()
    store.add("other", "resolve1-1", '{"verdict":"resolved"}')
    files, counts = export(store, kinds=("review",))
    assert "conflict.jsonl" not in files and counts["conflict"] == 0 and "conflict_skipped" not in counts
    counts["conflict"] = 1
    assert "conflict: 1" in training.report(counts)[1] and "conflict skipped" not in training.report(counts)[1]
