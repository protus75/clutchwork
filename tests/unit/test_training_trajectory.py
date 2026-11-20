import asyncio
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace as NS

import pytest

from clutch import __main__ as entry
from clutch import training
from clutch.config import TrainingData
from clutch.redact import Redactor


class Store:
    def __init__(self):
        self.start = NS(run_seq=2, attempt=3, call=4, surface="implement", provider=NS(adapter="ClaudeAdapter"), prompt=NS(blob="prompt"), engine=NS(version="v", spec="implement", spec_version="s"))
        self.blobs = {"prompt": b"prompt", "stdout": b"stream", "diff": b"diff --git a/src/app.py b/src/app.py\n+attempt"}
        self.end = NS(raw=NS(stdout="stdout"))

    def attempts(self):
        return [("ticket", 2, 3)]

    def read_attempt(self, *key):
        return NS(call_keys=["call"], diff_blob="diff", findings=[])

    def call_keys(self, prefix):
        return ["call"]

    def read_record(self, key, kind):
        if kind == "end" and self.end is None:
            raise FileNotFoundError(key)
        return self.start if kind == "start" else self.end

    def get_blob(self, key):
        if key not in self.blobs:
            raise FileNotFoundError(key)
        return self.blobs[key]


class Git:
    async def merged_tickets(self, repo):
        return [("sha", "ticket")]

    async def diff(self, repo, base, sha):
        return "diff --git a/src/app.py b/src/app.py\n+merged"


def event(seq, args, kind="tool_call"):
    return NS(seq=seq, kind=kind, tool=NS(class_="read", native="Read"), args=args, native={"private": "raw envelope"})


def render(store, **kwargs):
    files, counts = asyncio.run(training.render(store, Git(), Path("/repo"), Redactor({}), TrainingData(enabled=True, exclude=["private/*"]), **kwargs))
    return [json.loads(line) for line in files["sft.jsonl"].splitlines()], counts


def test_trajectory_and_attempts(monkeypatch):
    store = Store()
    calls = []

    def normalize(stdout, times_ns, put_blob):
        calls.append((stdout, times_ns, put_blob(b"content")))
        return [event(7, {"file_path": "src/app.py"}), event(8, {}, "message")]

    monkeypatch.setattr(training.claude, "normalize", normalize)
    rows, counts = render(store)
    assert [row["label"] for row in rows] == ["merged", "neutral"]
    assert [row["trajectory"] for row in rows] == [[{"seq": 7, "tool": "read", "native": "Read", "args": {"file_path": "src/app.py"}}]] * 2
    assert calls == [(b"stream", None, hashlib.sha256(b"content").hexdigest())] * 2
    assert counts["implement"] == 2
    rows, _ = render(store, trajectory=False)
    assert all("trajectory" not in row for row in rows)


def test_excluded_paths_and_secret(monkeypatch):
    store = Store()
    events = [event(1, {"file_path": ".env.local"}), event(2, {"file_path": "private/key.txt"}), event(3, {"file_path": "src/app.py"})]
    monkeypatch.setattr(training.claude, "normalize", lambda *a, **kw: events)
    rows, counts = render(store)
    assert [row["trajectory"] for row in rows] == [[{"seq": 3, "tool": "read", "native": "Read", "args": {"file_path": "src/app.py"}}]] * 2
    assert counts["dropped"] == 0
    events.append(event(4, {"command": "AKIA" + "A" * 16}))
    rows, counts = render(store)
    assert rows == [] and counts["dropped"] == 2


@pytest.mark.parametrize("missing", ["end", "stdout", "adapter"])
def test_missing_trajectory(monkeypatch, missing):
    store = Store()
    if missing == "end":
        store.end = None
    elif missing == "stdout":
        del store.blobs["stdout"]
    else:
        store.start.provider.adapter = "QwenAdapter"
    monkeypatch.setattr(training.claude, "normalize", lambda *a, **kw: pytest.fail("unexpected normalization"))
    rows, counts = render(store)
    assert len(rows) == 2 and all("trajectory" not in row for row in rows)
    assert counts["skipped"] == 0 and counts["dropped"] == 0


def test_parser_trajectory_flag():
    parser = entry._parser()
    assert parser.parse_args(["training", "export", "--out", "X", "--no-trajectory"]).trajectory is False
    assert parser.parse_args(["training", "export", "--out", "X"]).trajectory is True
