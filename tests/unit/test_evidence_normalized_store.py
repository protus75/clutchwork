"""Normalized view replacement, coexistence and tolerant version reads."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Normalized evidence versions and replacement
# relates: [tests/unit/test_evidence_views.py]
# owner: tests/unit/test_evidence_views.py
# verified: 75d75946
# hash: b22756c248beb437d6daf3a7a801b1c08840d3a094d9ed6b9e69a9bc1e7a1aee

from tests.unit.test_evidence_views import CLAUDE, memory_store, stored_view


def test_normalized_versions(tmp_path):
    store = memory_store(tmp_path)
    view = stored_view(store, "claude", CLAUDE)
    key = "llm/test/1/implement/0/1"
    old = {**view, "normalizer": "claude-stream/1", "events": []}
    store.write_normalized(key, old["normalizer"], old)
    store.write_normalized(key, view["normalizer"], {**view, "events": []})
    store.write_normalized(key, view["normalizer"], view)
    directory = store._record_path(key, "start").parent / "normalized"
    # Rules out append-only writes, unescaped slashes, deleting the old id, or retaining the first view.
    assert (store.fs.entries(directory), store.read_normalized(key)) == (["claude-stream%2F1.json", "claude-stream%2F2.json"], ([old, view], 0))
    future = {**view, "schema": "clutch.evidence.events/2.0"}
    store.write_normalized(key, "future/1", future)
    minor = {**view, "schema": "clutch.evidence.events/1.9", "future": True}
    store.write_normalized(key, "minor/1", minor)
    store.fs.write(directory / "ignored.txt", b"not json")
    # Rules out accepting unknown major versions, rejecting new minors, or reading non-JSON files.
    assert store.read_normalized(key) == ([old, view, minor], 1)
