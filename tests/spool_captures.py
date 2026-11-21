# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Read and write spool captures for tests.
# relates: [clutch/evidence/store.py]
# owner: engine
# verified: 23d3b116
# hash: 4f7bea7b0e0d2d9e5e72b391b97217df83562939856fb3575826b1df0d7df116
import re

from clutch.evidence.store import CaptureNotFound, CaptureUnreadable, EvidenceStore, capture_key
from clutch.seams import LocalFileSystem


def read_capture(state_dir, spool_stem, attempt, name, *, fs=None):
    key = capture_key(spool_stem, attempt, name)
    fs = fs or LocalFileSystem()
    store = EvidenceStore(state_dir, fs, fs.read_bytes, fs.size, lambda text: text)
    try:
        return store.get_capture(*key)
    except OSError as exc:
        raise CaptureUnreadable(str(exc)) from exc


def write_capture(state_dir, spool_stem, attempt, name, data, *, fs=None):
    key = capture_key(spool_stem, attempt, name)
    if not isinstance(data, bytes):
        raise ValueError("capture data must be bytes")
    fs = fs or LocalFileSystem()
    store = EvidenceStore(state_dir, fs, fs.read_bytes, fs.size, lambda text: text)
    store.put_capture(*key, data)


def list_captures(state_dir, spool_stem, attempt=None, *, fs=None):
    stem, _, name = capture_key(spool_stem, 0 if attempt is None else attempt, "x")
    fs = fs or LocalFileSystem()
    store = EvidenceStore(state_dir, fs, fs.read_bytes, fs.size, lambda text: text)
    prefix = name.removesuffix("x")
    return [(number, capture.removeprefix(prefix)) for number, capture in store.captures(stem, attempt) if (capture.startswith(prefix) if prefix else not re.match(r"run-[0-9]+/", capture))]
