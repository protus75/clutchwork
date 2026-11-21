# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: verify training export index joins
# relates: [clutch/__main__.py, clutch/config.py, clutch/redact.py, clutch/training.py, tests/unit/test_training_export.py]
# owner: engine
# verified: ee052b47
# hash: 6a1a6a1cb1e42eb4036fa6b02a0ce7a2dd92cacd02faab1ff19951115a524af0
import asyncio
import json
from pathlib import Path
from types import SimpleNamespace as NS

import duckdb
import pytest

from clutch import __main__ as entry
from clutch import training
from clutch.config import TrainingData
from clutch.redact import Redactor
from tests.unit.test_training_export import Git, Store, manifest

DIFF = "\n".join(f"diff --git a/{p} b/{p}" for p in ("clutch/b.py", "clutch/a.py", "docs/x.md", "new.py", "clutch/a.py"))
EXPECTED = [
    {"path": "clutch/a.py", "purpose": "parse a", "touches": 2},
    {"path": "clutch/b.py", "purpose": "", "touches": 1},
    {"path": "docs/x.md", "purpose": "guide", "touches": 0},
]


def database(path):
    conn = duckdb.connect(str(path))
    conn.execute("CREATE TABLE files (path VARCHAR, purpose VARCHAR)")
    conn.execute("CREATE TABLE touches (ticket VARCHAR, path VARCHAR)")
    conn.executemany("INSERT INTO files VALUES (?, ?)", [("clutch/a.py", "parse a"), ("clutch/b.py", None), ("docs/x.md", "guide"), (None, "ignored")])
    conn.executemany(
        "INSERT INTO touches VALUES (?, ?)", [("t1", "clutch/a.py"), ("t2", "clutch/a.py"), ("t0", "clutch/a.py"), ("t1", "clutch/a.py"), ("t1", "clutch/b.py"), (None, "docs/x.md"), ("t3", None)]
    )
    conn.close()


def render(index_marker=None, *, trajectory=False, secret=False, monkeypatch=None):
    store = Store()
    store.blobs["diff"] = DIFF.encode()
    store.manifests[("t0", 1, 1)] = manifest()
    store.manifests[("t0", 1, 1)].outcome = "rejected"

    class DiffGit(Git):
        async def diff(self, repo, base, sha):
            return DIFF

    if trajectory:
        monkeypatch.setattr(training, "_trajectory", lambda *args: [{"seq": 17}])
    kwargs = {} if index_marker is None else {"index": index_marker}
    files, counts = asyncio.run(
        training.render(
            store,
            DiffGit(("t0",)),
            Path("/repo"),
            Redactor({"key": "hidden-secret"} if secret else {}),
            TrainingData(enabled=True),
            lambda p: b"",
            kinds=("implement", "preference", "review"),
            **kwargs,
        )
    )
    return {name: [json.loads(line) for line in data.splitlines()] for name, data in files.items()}, counts


def test_join_and_layout(tmp_path, monkeypatch):
    path = tmp_path / "index.duckdb"
    database(path)
    index = training.index_files(path, lambda p: p.stat().st_size)
    rows, counts = render(index, trajectory=True, monkeypatch=monkeypatch)
    assert len(rows["sft.jsonl"]) == 2 and counts["implement"] == 2
    for row in rows["sft.jsonl"]:
        assert row["file_purposes"] == EXPECTED
        assert list(row).index("file_purposes") == list(row).index("trajectory") + 1
    rows, _ = render(index)
    assert all(list(row)[-1] == "file_purposes" for row in rows["sft.jsonl"])
    assert len(rows["preference.jsonl"]) == 1 and len(rows["review.jsonl"]) == 1
    assert all("file_purposes" not in row for name in ("preference.jsonl", "review.jsonl") for row in rows[name])
    baseline, _ = render()
    for empty in (None, {}, {"unrelated": ("other", frozenset())}):
        result, _ = render(empty)
        assert result == baseline
        assert all("file_purposes" not in row for row in result["sft.jsonl"])
    index["clutch/a.py"] = ("hidden-secret", frozenset())
    rows, counts = render(index, secret=True)
    assert rows["sft.jsonl"] == [] and counts["dropped"] == 2


def test_unreadable(tmp_path):
    def size(p):
        return p.stat().st_size

    assert training.index_files(tmp_path / "missing", size) == {}
    assert training.index_files(tmp_path, size) == {}
    path = tmp_path / "incomplete.duckdb"
    conn = duckdb.connect(str(path))
    conn.execute("CREATE TABLE files (path VARCHAR, purpose VARCHAR)")
    conn.close()
    assert training.index_files(path, size) == {}

    def broken(*args, **kwargs):
        raise duckdb.IOException("locked")

    assert training.index_files(path, size, connect=broken) == {}


def test_handler(tmp_path, monkeypatch):
    state = tmp_path / "state"
    state.mkdir()
    path = state / "index.duckdb"
    database(path)
    config = NS(state_dir=state, training_data=TrainingData(enabled=True), providers=[], release=NS(pypi_token="TOKEN"))
    monkeypatch.setattr(entry, "load_config", lambda *args, **kwargs: config)
    monkeypatch.setattr(entry, "Git", lambda *args, **kwargs: object())
    received = []

    async def capture(*args, **kwargs):
        received.append(kwargs["index"])
        return {}, dict(implement=0, preference=0, review=0, diagnosis=0, ticket=0, conflict=0, triage=0, dropped=0, skipped=0, heldout=0)

    monkeypatch.setattr(training, "render", capture)
    assert entry.main(["training", "export", "--out", str(tmp_path / "out")], cwd=tmp_path, env={}) == 0
    assert received[-1]["clutch/a.py"] == ("parse a", frozenset({"t0", "t1", "t2"}))
    path.unlink()
    assert entry.main(["training", "export", "--out", str(tmp_path / "out")], cwd=tmp_path, env={}) == 0
    assert received[-1] == {}
