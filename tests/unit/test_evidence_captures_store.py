"""Capture persistence, validation and retention."""

import json

import pytest

from clutch.evidence.store import CaptureNotFound, CaptureUnreadable
from tests.unit.test_evidence_views import memory_store


def test_put_overwrite_and_listing(tmp_path):
    store = memory_store(tmp_path)
    store.put_capture("my-ticket", 2, "implement/prompt.md", b"error: boom")
    assert store.get_capture("my-ticket", 2, "implement/prompt.md") == b"error: boom"
    store.put_capture("my-ticket", 2, "implement/prompt.md", b"new")
    store.put_capture("my-ticket", 2, "a.txt", b"two")
    store.put_capture("my-ticket", 10, "a.txt", b"ten")
    root = store.root / "captures/my-ticket"
    assert store.get_capture("my-ticket", 2, "implement/prompt.md") == b"new"
    assert root / "2/implement%2Fprompt.md.json" in store.fs.files
    store.fs.write(root / "abc/a.json", b"{}")
    store.fs.write(root / "0/a.json", b"{}")
    store.fs.write(root / "2/%20.json", b"{}")
    assert store.captures("my-ticket") == [(2, "a.txt"), (2, "implement/prompt.md"), (10, "a.txt")]
    assert store.captures("my-ticket", 2) == [(2, "a.txt"), (2, "implement/prompt.md")]


@pytest.mark.parametrize(
    "field,value", [("stem", x) for x in ["Bad Stem", "", "../x"]] + [("attempt", x) for x in [0, -1, True, "1"]] + [("name", x) for x in ["", "/a", ".hidden", "a b", "a\nb", "..", "a" * 201]]
)
def test_invalid_fields_never_write(tmp_path, field, value):
    store = memory_store(tmp_path)
    args = {"stem": "my-ticket", "attempt": 1, "name": "a.txt"}
    args[field] = value
    with pytest.raises(ValueError):
        store.put_capture(**args, data=b"payload")
    assert not store.fs.files
    with pytest.raises(ValueError):
        store.get_capture(**args)
    if field != "name":
        with pytest.raises(ValueError):
            store.captures(args["stem"], args["attempt"])


def test_pointer_validation_and_missing_blob(tmp_path):
    store = memory_store(tmp_path)
    with pytest.raises(CaptureNotFound):
        store.get_capture("my-ticket", 1, "a.txt")
    store.put_capture("my-ticket", 1, "a.txt", b"payload")
    path = store.root / "captures/my-ticket/1/a.txt.json"
    valid = json.loads(store.fs.read_bytes(path))
    for raw in [b"{", b"[1]", json.dumps({**valid, "schema": "clutch.evidence.capture/2.0"}).encode(), json.dumps({**valid, "blob": "nope"}).encode()]:
        store.fs.write(path, raw)
        with pytest.raises(CaptureUnreadable):
            store.get_capture("my-ticket", 1, "a.txt")
    store.fs.write(path, json.dumps({**valid, "schema": "clutch.evidence.capture/1.3"}).encode())
    assert store.get_capture("my-ticket", 1, "a.txt") == b"payload"
    store.fs.remove(store._blob_path(valid["blob"]))
    with pytest.raises(CaptureUnreadable) as exc:
        store.get_capture("my-ticket", 1, "a.txt")
    assert isinstance(exc.value.__cause__, FileNotFoundError)


def test_prune_preserves_capture_reference(tmp_path):
    store = memory_store(tmp_path)
    store.put_capture("my-ticket", 1, "a.txt", b"shared")
    shared = store.put_blob(b"shared")
    old = store.put_blob(b"old only")
    for key, ref in [("a", shared), ("b", old)]:
        store.fs.write(store.root / "calls" / key / "end.json", json.dumps({"clock": {"wall_end": key}, "raw": {"stdout": ref}}).encode())
    store.prune(0)
    assert store.get_capture("my-ticket", 1, "a.txt") == b"shared"
    with pytest.raises(FileNotFoundError):
        store.get_blob(old)


def test_redaction_and_corrupt_blob(tmp_path):
    from compression import zstd

    store = memory_store(tmp_path)
    store.redact = lambda text: text.replace("secret", "[redacted]")
    store.put_capture("my-ticket", 1, "a.txt", b"secret data")
    assert store.get_capture("my-ticket", 1, "a.txt") == b"[redacted] data"
    pointer = json.loads(store.fs.read_bytes(store.root / "captures/my-ticket/1/a.txt.json"))
    store.fs.write(store._blob_path(pointer["blob"]), b"corrupt")
    with pytest.raises(CaptureUnreadable) as exc:
        store.get_capture("my-ticket", 1, "a.txt")
    assert isinstance(exc.value.__cause__, zstd.ZstdError)
