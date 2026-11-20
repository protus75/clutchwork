import asyncio
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace as NS

import pytest

from clutch import __main__ as entry
from clutch import training
from clutch.config import TrainingData
from clutch.evidence.store import SKIP
from clutch.redact import Redactor


def call(run=1, attempt=1, call=1, surface="implement", blob="prompt"):
    return NS(run_seq=run, attempt=attempt, call=call, surface=surface, provider=NS(adapter="ClaudeAdapter"), prompt=NS(blob=blob), engine=NS(version="engine", spec="implement", spec_version="v1"))


class Store:
    def __init__(self):
        self.starts = {"old": call(), "new": call(2), "other": call(surface="review")}
        self.blobs = {"prompt": b"the prompt", "diff": b"diff --git a/file b/file\n+change"}
        self.manifests = {}

    def attempts(self):
        return sorted(self.manifests)

    def read_attempt(self, *key):
        return self.manifests[key]

    def read_record(self, key, kind):
        if kind == "end" or key not in self.starts:
            raise FileNotFoundError(key)
        return self.starts[key]

    def call_keys(self, prefix):
        return list(self.starts)

    def get_blob(self, key):
        if key not in self.blobs:
            raise FileNotFoundError(key)
        return self.blobs[key]


class Git:
    def __init__(self, stems=("a",)):
        self.stems = stems

    async def merged_tickets(self, repo):
        return [("sha-" + stem, stem) for stem in self.stems]

    async def diff(self, repo, base, sha):
        assert base == sha + "^"
        return "diff --git a/file b/file\n+merged"


def manifest(code="logic"):
    return NS(call_keys=["old", "other"], diff_blob="diff", findings=[{"code": code, "message": "finding"}])


def export(store, git=None, kinds=("implement", "preference"), holdout=0, redactor=None):
    return asyncio.run(training.render(store, git or Git(), Path("/repo"), redactor or Redactor({}), TrainingData(enabled=True), kinds, holdout))


def test_records_and_pairing():
    store = Store()
    store.manifests[("a", 1, 1)] = manifest()
    store.manifests[("b", 1, 1)] = manifest("rma")
    store.manifests[("c", 1, 1)] = NS(call_keys=["old"], diff_blob="diff", findings=[])
    files, counts = export(store)
    rows = [json.loads(line) for line in files["sft.jsonl"].splitlines()]
    assert [(r["stem"], r["label"]) for r in rows] == [("a", "negative"), ("a", "merged"), ("b", "neutral"), ("c", "neutral")]
    assert all("trajectory" not in row for row in rows)
    assert rows[1]["run_seq"] == 2
    assert rows[1]["messages"][1]["content"].endswith("+merged")
    pair = json.loads(files["preference.jsonl"])
    assert (pair["prompt"], pair["chosen"].splitlines()[-1], pair["rejected"].splitlines()[-1], pair["reason"]) == ("the prompt", "+merged", "+change", "finding")
    assert counts["preference"] == 1
    assert export(store)[0] == files
    assert list(export(store, kinds=("preference",))[0]) == ["preference.jsonl"]


def test_scrub_and_holdout():
    store = Store()
    for text in ("AKIA" + "A" * 16, "-----BEGIN RSA PRIVATE KEY-----", "Bearer " + "x" * 20, "secret"):
        store.blobs["prompt"] = text.encode()
        files, counts = export(store, redactor=Redactor({"key": "secret"}))
        assert not files["sft.jsonl"] and counts["dropped"] == 1
    store.blobs["prompt"] = b"prompt"
    for header in ("diff --git a/.env.local b/.env.local", "diff --git a/deploy/id_rsa.pub b/deploy/id_rsa.pub", "diff --git broken"):
        store.blobs["diff"] = header.encode()
        store.manifests[("b", 1, 1)] = manifest()
        files, counts = export(store)
        assert len(files["sft.jsonl"].splitlines()) == 1 and counts["dropped"] == 1
    stems = [f"stem{i}" for i in range(20)]
    store.manifests = {}
    files, counts = export(store, Git(stems), holdout=50)
    held = sorted(s for s in stems if int(hashlib.sha256(s.encode()).hexdigest(), 16) % 100 < 50)
    assert files["holdout.txt"].decode().splitlines() == held
    assert {json.loads(line)["stem"] for line in files["sft.jsonl"].splitlines()} == set(stems) - set(held)
    assert counts["heldout"] == len(held) and export(store, Git(stems), holdout=50)[0] == files
    assert "holdout.txt" not in export(store, Git(stems))[0]
    assert not export(store, Git(stems), holdout=100)[0]["sft.jsonl"]


def test_missing_and_skipped():
    store = Store()
    store.starts = {"skip": SKIP}
    store.manifests[("b", 1, 1)] = manifest()
    files, counts = export(store)
    assert files["sft.jsonl"] == b"" and counts["skipped"] == 2
    store.manifests[("b", 1, 1)] = SKIP
    assert export(store)[1]["skipped"] == 1


def test_report_and_disabled(tmp_path, capsys, monkeypatch):
    lines = training.report(dict(implement=1, preference=2, dropped=3, skipped=4, heldout=5))
    assert lines[0] == training.NOTICE and len(lines) == 2 and all(str(i) in lines[1] for i in range(1, 6))
    config = NS(state_dir=tmp_path / "state", training_data=TrainingData(), providers=[], release=NS(pypi_token="TOKEN"))
    monkeypatch.setattr(entry, "load_config", lambda *args, **kwargs: config)
    assert entry.main(["training", "export", "--out", str(tmp_path / "out")], cwd=tmp_path, env={}) == 2
    assert "set training_data.enabled: true" in capsys.readouterr().err
    assert not list(tmp_path.iterdir())


def test_handler_success(tmp_path, capsys, monkeypatch):
    config = NS(state_dir=tmp_path / "state", training_data=TrainingData(enabled=True), providers=[], release=NS(pypi_token="TOKEN"))
    monkeypatch.setattr(entry, "load_config", lambda *args, **kwargs: config)

    class EmptyGit:
        def __init__(self, *args, **kwargs):
            pass

        async def merged_tickets(self, repo):
            return []

    monkeypatch.setattr(entry, "Git", EmptyGit)
    out = tmp_path / "out"
    assert entry.main(["training", "export", "--out", str(out)], cwd=tmp_path, env={}) == 0
    stdout, stderr = capsys.readouterr()
    assert stdout.splitlines() == training.report(dict(implement=0, preference=0, dropped=0, skipped=0, heldout=0))
    assert stderr == ""
    assert {p.name: p.read_bytes() for p in out.iterdir()} == {"sft.jsonl": b"", "preference.jsonl": b""}
