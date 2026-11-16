import json

import pytest

from clutch.evidence.store import EvidenceStore
from clutch.seams import LocalFileSystem


def test_read_bytes_returns_exact_bytes(tmp_path):
    fs = LocalFileSystem()
    path = tmp_path / "bytes"
    fs.write(path, b"\x00\xffabc\n")
    assert fs.read_bytes(path) == b"\x00\xffabc\n"


def test_size_counts_bytes(tmp_path):
    fs = LocalFileSystem()
    path = tmp_path / "bytes"
    fs.write(path, b"\x00\xffabc\n")
    assert fs.size(path) == 6
    fs.write(path, "é".encode("utf-8"))
    assert fs.size(path) == 2


def test_absent_path_raises(tmp_path):
    fs = LocalFileSystem()
    path = tmp_path / "absent"
    with pytest.raises(FileNotFoundError):
        fs.read_bytes(path)
    with pytest.raises(FileNotFoundError):
        fs.size(path)


def test_evidence_store_reads_through_the_seam(tmp_path):
    fs = LocalFileSystem()
    store = EvidenceStore(tmp_path, fs, fs.read_bytes, fs.size, lambda s: s)
    ref = store.put_blob(b"payload")
    assert store.get_blob(ref) == b"payload"
    digest = ref.removeprefix("sha256:")
    blob = tmp_path / "evidence" / "blobs" / digest[:2] / digest
    record = {"clock": {"wall_end": "2026-01-01T00:00:00+00:00"}, "raw": {"stdout": ref}}
    fs.publish(tmp_path / "evidence" / "calls" / "key" / "end.json", json.dumps(record).encode())
    store.prune(0)
    assert not blob.exists()
