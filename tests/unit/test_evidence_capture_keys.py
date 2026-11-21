"""Spool slot mapping to evidence capture keys."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Verify spool capture key mapping and refusals.
# relates: [clutch/evidence/store.py, tests/unit/test_evidence_views.py]
# owner: engine
# verified: 8373ae09
# hash: c6c0c17793f73674e7bdd709f7c24b75511a885b5ade6d80c7bd9ee9c94bf3e5

import pytest

from clutch.evidence.store import capture_key
from tests.unit.test_evidence_views import memory_store


@pytest.mark.parametrize(
    "slot,attempt,name,expected",
    [
        ("my-ticket", 0, "merge/host-01.txt", ("my-ticket", 0, "merge/host-01.txt")),
        ("my-ticket", 1, "implement/call-01/prompt.md", ("my-ticket", 1, "implement/call-01/prompt.md")),
        ("semantic", 0, "merge-integration/verify-01.txt", ("semantic", 0, "merge-integration/verify-01.txt")),
        ("review_visual", 2, "review_visual/call-01/output.txt", ("review_visual", 2, "review_visual/call-01/output.txt")),
        ("work", 1, "render/a.txt", ("work", 1, "render/a.txt")),
        ("work/1", 1, "review/call-01/output.txt", ("work", 1, "run-1/review/call-01/output.txt")),
        ("author/8", 0, "requisition_review/call-01/prompt.md", ("author", 0, "run-8/requisition_review/call-01/prompt.md")),
        ("review-" + "a" * 64, 0, "x", ("review-" + "a" * 64, 0, "x")),
        ("work/0", 2, "x", ("work", 2, "run-0/x")),
    ],
)
def test_mapping_round_trip(tmp_path, slot, attempt, name, expected):
    store = memory_store(tmp_path)
    key = capture_key(slot, attempt, name)
    assert key == expected
    store.put_capture(*key, b"payload")
    assert store.get_capture(*key) == b"payload"
    assert store.captures(key[0]) == [(key[1], key[2])]


def test_run_sequences_are_distinct():
    assert capture_key("work/1", 1, "x") != capture_key("work/2", 1, "x")


@pytest.mark.parametrize(
    "slot,attempt,name",
    [(s, 1, "a") for s in ["", "a/b/c", "/8", "Work/1", None, 5, "author/", "work/01", "work/-1", "work/x", "work/1234567890", "work/١"]]
    + [("work", a, "a") for a in [-1, True, "0"]]
    + [("work", 1, ""), ("work", 1, "/a"), ("work/1", 1, "a" * 200), ("work", 1, "run-1/a.txt")],
)
def test_refused_key(slot, attempt, name):
    with pytest.raises(ValueError):
        capture_key(slot, attempt, name)
