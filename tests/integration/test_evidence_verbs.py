"""Evidence commands over real stored calls and the golden Codex stream."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Tests the evidence schema, show, renormalize and coverage CLI verbs over stored calls and the golden Codex stream, including pruned, unknown-version and corrupt inputs
# relates: [clutch/__main__.py, clutch/evidence/schema.py, clutch/evidence/store.py, clutch/seams.py, tests/evidence_records.py, tests/integration/test_cli.py]
# owner: engine
# verified: d32c32ad
# hash: 2176ece0f9876bc690517c843a24b110f7efc60aa136114917d39001f9186790

import json
from pathlib import Path

import pytest

from clutch.__main__ import main
from clutch.evidence.schema import json_schema
from clutch.evidence.store import EvidenceStore
from clutch.seams import LocalFileSystem
from tests.evidence_records import seed_end
from tests.integration.test_cli import CONFIG
from tests.unit.test_evidence_views import start_record

pytestmark = pytest.mark.disk_io_skip


def setup(tmp_path):
    (tmp_path / "config.yaml").write_text(CONFIG)
    fs = LocalFileSystem()
    return EvidenceStore(tmp_path / ".clutch/state", fs, fs.read_bytes, fs.size, lambda text: text)


def seed(store, key, provider="codex", stdout=b'{"type":"thread.started"}\n'):
    seed_end(store.root.parent, key, stdout.decode(), "2026-01-01")
    start = start_record(provider).model_dump(by_alias=True)
    start["id"] = key
    store.write_record(key, "start", start)
    path = store._record_path(key, "end")
    end = json.loads(path.read_bytes())
    end["raw"]["stdout_times"] = store.put_blob(json.dumps([17_000_000 + i * 1_000_000 for i in range(len(stdout.splitlines()))]).encode())
    store.fs.write(path, json.dumps(end).encode())


def test_schema_and_unknown_key(tmp_path, capsys):
    store = setup(tmp_path)
    before = list(tmp_path.rglob("*"))
    # Rules out printing a hand-written schema or creating evidence/journal/lock files.
    assert main(["evidence", "schema", "event"], cwd=tmp_path) == 0
    assert json.loads(capsys.readouterr().out) == json_schema("event")
    assert list(tmp_path.rglob("*")) == before
    # Rules out a traceback or success for an unknown call.
    assert main(["evidence", "show", "missing"], cwd=tmp_path) == 2
    output = capsys.readouterr()
    assert " -- " in output.err and "Traceback" not in output.err
    assert not store.root.exists()


def test_renormalize_show_and_coverage(tmp_path, capsys):
    store = setup(tmp_path)
    raw = (Path(__file__).resolve().parents[1] / "fixtures/evidence/codex/stream.jsonl").read_bytes()
    key = "llm/test/1/implement/0/1"
    seed(store, key, stdout=raw)
    before = {p: p.read_bytes() for p in store.root.rglob("*") if p.is_file()}
    for _ in range(2):
        assert main(["evidence", "renormalize", "--prefix", "llm/test/"], cwd=tmp_path) == 0
        assert capsys.readouterr().out == "normalized: 1, skipped: 0\n"
    stored, skipped = store.read_normalized(key)
    # Rules out no events, discarded arrival offsets, and changed original envelopes/raw blobs.
    assert (len(stored), skipped, stored[0]["events"][0]["t_ms"]) == (1, 0, 17)
    assert {p: p.read_bytes() for p in before} == before
    assert main(["evidence", "show", key], cwd=tmp_path) == 0
    output = capsys.readouterr().out
    assert "start.json:" in output and "end.json:" in output and "0 17 session_start thread.started" in output
    assert main(["evidence", "coverage"], cwd=tmp_path) == 0
    output = capsys.readouterr().out
    assert "codex 1.2:" in output and "% known; unknown:" in output and "skipped (unknown major version): 0" in output
    assert not (store.root.parent / "journal").exists()
    assert not (store.root.parent / "clutch.lock").exists()


@pytest.mark.parametrize("missing", ["stdout", "stdout_times", "end"])
def test_renormalize_skips_pruned_or_incomplete_calls(tmp_path, capsys, missing):
    store = setup(tmp_path)
    seed(store, "a-pruned")
    seed(store, "b-good", stdout=b'{"type":"thread.started","thread_id":"other"}\n')
    end = store.read_record("a-pruned", "end")
    store.fs.remove(store._record_path("a-pruned", "end") if missing == "end" else store._blob_path(getattr(end.raw, missing)))
    # stdout_times is shared; replace the good call's arrival times when pruning that blob.
    if missing == "stdout_times":
        path = store._record_path("b-good", "end")
        good = json.loads(path.read_bytes())
        good["raw"]["stdout_times"] = store.put_blob(b"[18000000]")
        store.fs.write(path, json.dumps(good).encode())
    assert main(["evidence", "renormalize"], cwd=tmp_path) == 0
    assert capsys.readouterr().out == "normalized: 1, skipped: 1\n"
    assert len(store.read_normalized("b-good")[0]) == 1


def test_unknown_versions_provider_and_unreadable_store(tmp_path, capsys):
    store = setup(tmp_path)
    seed(store, "a-unknown", "unsupported")
    seed(store, "b-future")
    path = store._record_path("b-future", "start")
    data = json.loads(path.read_bytes())
    data["schema"] = "clutch.evidence.call/2.0"
    store.fs.write(path, json.dumps(data).encode())
    assert main(["evidence", "renormalize"], cwd=tmp_path) == 0
    assert capsys.readouterr().out == "normalized: 0, skipped: 2\n"
    assert main(["evidence", "coverage"], cwd=tmp_path) == 0
    assert "skipped (unknown major version): 1" in capsys.readouterr().out
    path.write_bytes(b"invalid json")
    assert main(["evidence", "coverage"], cwd=tmp_path) == 2
    output = capsys.readouterr().err
    assert " -- " in output and "Traceback" not in output


def test_corrupt_blob_refuses(tmp_path, capsys):
    store = setup(tmp_path)
    seed(store, "corrupt")
    end = store.read_record("corrupt", "end")
    store._blob_path(end.raw.stdout).write_bytes(b"not zstd")
    # Rules out allowing a decompression traceback to escape the command boundary.
    assert main(["evidence", "renormalize"], cwd=tmp_path) == 2
    output = capsys.readouterr().err
    assert " -- " in output and "Traceback" not in output
