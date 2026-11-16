import hashlib
import json

from clutch.evidence.store import EvidenceStore
from clutch.seams import LocalFileSystem


class CountingFS(LocalFileSystem):
    def __init__(self):
        self.publishes = 0
        self.removed = []

    def publish(self, path, data):
        self.publishes += 1
        super().publish(path, data)

    def remove(self, path):
        self.removed.append(path)
        super().remove(path)


def make_store(tmp_path):
    fs = CountingFS()
    return EvidenceStore(tmp_path, fs, lambda p: p.read_bytes(), lambda p: p.stat().st_size, lambda s: s.replace("secret", "[redacted]")), fs


def test_blobs_round_trip_and_redact(tmp_path):
    store, fs = make_store(tmp_path)
    ref = store.put_blob(b"a secret message")
    assert ref == "sha256:" + hashlib.sha256(b"a [redacted] message").hexdigest()
    assert store.put_blob(b"a secret message") == ref
    assert fs.publishes == 1
    assert store.get_blob(ref) == b"a [redacted] message"
    binary = b"\xff\x00\xfe"
    assert store.get_blob(store.put_blob(binary)) == binary


def test_prune_protects_newer_and_inflight_references(tmp_path):
    store, fs = make_store(tmp_path)
    old, shared, inflight, newer, newest = [store.put_blob(bytes([65 + i]) * 200) for i in range(5)]
    calls = store.root / "calls"

    def put(call, name, data):
        fs.publish(calls / call / name, json.dumps(data).encode())

    put("a", "end.json", {"clock": {"wall_end": "2020"}, "raw": [old, shared, inflight]})
    put("b", "start.json", {"prompt": {"blob": shared}})
    put("b", "end.json", {"clock": {"wall_end": "2021"}, "raw": [newer]})
    put("c", "end.json", {"clock": {"wall_end": "2022"}, "raw": [newest]})
    put("active", "start.json", {"prompt": {"blob": inflight}})
    put("c", "normalized/view.json", [{"text_blob": shared}])
    total = sum(store.size(store._blob_path(ref)) for ref in (old, shared, inflight, newer, newest))
    store.prune(total - store.size(store._blob_path(old)))
    assert fs.removed == [store._blob_path(old)]
    assert store.get_blob(shared) == b"B" * 200
    assert store.get_blob(inflight) == b"C" * 200
    assert store.get_blob(newer) == b"D" * 200
    assert store.get_blob(newest) == b"E" * 200
    assert len(fs.entries(calls / "a")) == 1


def test_prune_below_bound_and_invalid_reference(tmp_path):
    import pytest

    store, fs = make_store(tmp_path)
    ref = store.put_blob(b"kept")
    store.prune(1000)
    assert store.get_blob(ref) == b"kept"
    assert fs.removed == []
    with pytest.raises(ValueError):
        store.get_blob("sha256:../bad")
