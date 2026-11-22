"""A starvation barrier reserves only its own fence."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Unit tests that a fill_slots starvation barrier reserves only its own fence: disjoint candidates pass, overlapping ones wait, and the barrier starts first once clear
# relates: [clutch/drain.py, clutch/tickets.py]
# owner: engine
# verified: 62301251
# hash: 6a79f6b7528ff172465dde9a283a84cb6aaafb8eb457375ac074a93b5ea38317

from clutch.drain import SKIP_LIMIT, fill_slots
from clutch.tickets import Frontmatter, Ticket


def ticket(stem, *fences):
    return Ticket(
        stem=stem,
        frontmatter=Frontmatter(state="confirmed", source="human", priority="P1", kind="bug"),
        sections={},
        depends=(),
        context=(),
        on_demand=(),
        scope_fence=fences,
        verification=(),
        expected_minutes=20,
        stuck_minutes=40,
        runs_before=(),
    )


def test_disjoint_candidate_passes_barrier():
    busy, blocked, later = ticket("busy", "src"), ticket("blocked", "src/file"), ticket("later", "docs")
    selected, _ = fill_slots([blocked, later], [busy], 1, [], {"blocked": SKIP_LIMIT}, set())
    assert selected == [later]


def test_barrier_holds_candidate_overlapping_only_it():
    busy, blocked, later = ticket("busy", "a"), ticket("blocked", "a", "b"), ticket("later", "b")
    selected, counts = fill_slots([blocked, later], [busy], 1, [], {"blocked": SKIP_LIMIT}, set())
    assert selected == []
    assert counts["later"] == 1


def test_barrier_starts_first_when_inflight_overlap_clears():
    blocked, later = ticket("blocked", "a", "b"), ticket("later", "b")
    selected, _ = fill_slots([blocked, later], [], 1, [], {"blocked": SKIP_LIMIT}, set())
    assert selected == [blocked]
