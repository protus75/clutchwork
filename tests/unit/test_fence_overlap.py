"""Fence matching and scheduling overlap use the same path boundaries."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Fence matching and scheduling overlap use the same path boundaries.
# relates: [clutch/stages.py, clutch/tickets.py]
# owner: engine
# verified: 0a308920
# hash: ac389dd3b68f9ebf1b8a7593f809d3a1242f1734eac012fd7360ac3b1d4b569c

import pytest

import clutch.stages as stages
from clutch.tickets import Frontmatter, GateBypass, Ticket, fences_overlap, in_fence, runs_alone


def ticket(stem, paths, bypass=None):
    return Ticket(
        stem=stem,
        frontmatter=Frontmatter(state="confirmed", source="human", priority="P2", kind="feature", gate_bypass=bypass or []),
        sections={},
        depends=(),
        context=(),
        on_demand=(),
        scope_fence=tuple(paths),
        verification=(),
        expected_minutes=20,
        stuck_minutes=40,
    )


@pytest.mark.parametrize(
    ("path", "prefix", "expected"),
    [
        ("a/b.py", "a", True),
        ("ab.py", "a", False),
        ("a", "a", True),
        ("a", "a/", False),
        ("a/x", "a/", True),
    ],
)
def test_in_fence(path, prefix, expected):
    assert in_fence(path, [prefix]) is expected


def test_old_owner_removed():
    assert not hasattr(stages, "_in_fence")


@pytest.mark.parametrize(
    ("left", "right", "expected"),
    [
        ("clutch", "clutch/tickets.py", True),
        ("clutch/tickets.py", "clutch", True),
        ("clutch/tickets.py", "clutch/tickets.py", True),
        ("clutch/tickets.py", "clutch/tickets_x.py", False),
        ("clutch/x.py", "docs/x.md", False),
        ("tickets", "clutch/x.py", True),
        ("clutch/x.py", "tickets/other/ticket.md", True),
        ("tickets/one/ticket.md", "tickets/two/ticket.md", False),
        ("tickets/one", "tickets/two", False),
        ("tickets/one/ticket.md", "clutch/x.py", False),
        ("clutch/x.py", "tickets/two/ticket.md", False),
    ],
)
def test_overlap(left, right, expected):
    assert fences_overlap(ticket("one", [left]), ticket("two", [right]), [], set()) is expected


def test_shared_and_run_alone():
    path = "docs/how-clutch-works.md"
    plain = ticket("one", ["docs"])
    other = ticket("two", [path])
    bypass = [GateBypass(code="scope_fence", reason="unbounded")]
    assert fences_overlap(plain, other, [], set())
    assert not fences_overlap(plain, other, [path], set())
    assert fences_overlap(ticket("one", ["docs"], bypass), other, [path], set())
    assert fences_overlap(plain, ticket("two", [path], bypass), [path], set())


def test_runs_alone():
    assert runs_alone(ticket("one", [], [GateBypass(code="scope_fence", reason="unbounded")]))
    assert not runs_alone(ticket("one", []))
    assert not runs_alone(ticket("one", [], [GateBypass(code="diff_budget", reason="large")]))
