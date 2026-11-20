import asyncio
import json
from pathlib import Path
from types import SimpleNamespace as NS

from clutch import training
from clutch.config import TrainingData
from clutch.redact import Redactor


class Store:
    def __init__(self):
        self.starts = {}
        self.manifests = {}
        self.blobs = {"prompt": b"specific prompt", "diff": b"diff --git a/a b/a\n+attempt"}

    def add(self, stem, surface, run=1, day="2026-11-10", blob="prompt"):
        key = f"llm/{stem}/{run}/{surface}/1/1"
        self.starts[key] = NS(
            run_seq=run,
            attempt=1,
            call=1,
            surface=surface,
            clock=NS(wall_start=day + "T23:59:59Z"),
            prompt=NS(blob=blob),
            provider=NS(adapter="ClaudeAdapter"),
            engine=NS(version="v", spec=surface, spec_version="1"),
        )
        return key

    def attempts(self):
        return sorted(self.manifests)

    def read_attempt(self, *key):
        return self.manifests[key]

    def read_record(self, key, kind):
        if kind == "end" or key not in self.starts:
            raise FileNotFoundError(key)
        return self.starts[key]

    def call_keys(self, prefix):
        return [key for key in self.starts if key.startswith(prefix)]

    def get_blob(self, key):
        return self.blobs[key]


class Git:
    async def merged_tickets(self, repo):
        return [("sha", "merged")]

    async def diff(self, repo, base, sha):
        return "diff --git a/a b/a\n+merged"


def export(store, files=None, **kwargs):
    def reader(path):
        if path.parent.name not in (files or {}):
            raise FileNotFoundError(path)
        return files[path.parent.name]

    return asyncio.run(training.render(store, Git(), Path("/repo"), Redactor({}), TrainingData(enabled=True), reader, **kwargs))


def rows(files, kind):
    return [json.loads(line) for line in files[kind + ".jsonl"].splitlines()]


def test_review_and_diagnosis():
    store = Store()
    review = store.add("merged", "review")
    store.manifests[("merged", 1, 1)] = NS(call_keys=[review], findings=[{"code": "logic", "message": "wrong"}], outcome="snag", diff_blob="diff")
    store.manifests[("other", 1, 1)] = NS(call_keys=[], findings=[], outcome="approve", diff_blob="diff")
    for stem in ("merged", "other", "missing"):
        store.add(stem, "diagnose")
    files, counts = export(store, {"merged": b'{"why": 1}', "other": b'{"why": 2}'}, kinds=("review", "diagnosis"))
    review_rows = rows(files, "review")
    assert len(review_rows) == 1 and review_rows[0]["label"] == "negative"
    assert json.loads(review_rows[0]["messages"][1]["content"]) == {"outcome": "snag", "findings": [{"code": "logic", "message": "wrong"}]}
    assert [(r["stem"], r["label"], r["messages"][1]["content"]) for r in rows(files, "diagnosis")] == [("merged", "merged", '{"why": 1}'), ("other", "neutral", '{"why": 2}')]
    assert counts["skipped"] == 1


def test_since_conflict_holdout_and_scrub():
    store = Store()
    for stem, day in (("old", "2026-11-09"), ("new", "2026-11-10")):
        implement = store.add(stem, "implement", day=day)
        review = store.add(stem, "review", day=day)
        store.manifests[(stem, 1, 1)] = NS(call_keys=[implement, review], findings=[{"code": "logic"}], outcome="snag", diff_blob="diff")
        store.add(stem, "resolve")
        store.add(stem, "diagnose")
    files, counts = export(store, {"old": b"old", "new": b"new"}, kinds=("implement", "review", "diagnosis"), since="2026-11-10")
    assert [r["stem"] for r in rows(files, "sft")] == ["new"]
    assert [r["stem"] for r in rows(files, "review")] == ["new"]
    assert counts["conflict_skipped"] == 2 and "conflict.jsonl" not in files
    assert "conflict skipped: 2" in training.report(counts)[1]
    held, _ = export(store, {"old": b"old", "new": b"new"}, kinds=("review", "diagnosis"), holdout=100)
    assert not rows(held, "review") and not rows(held, "diagnosis")
    store.blobs["prompt"] = ("Bearer " + "x" * 20).encode()
    dropped, counts = export(store, {"old": b"old", "new": b"new"}, kinds=("review",), since="2026-11-10")
    assert not rows(dropped, "review") and counts["dropped"] == 1
