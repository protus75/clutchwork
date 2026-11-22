"""Parallel ordering and conflict-aware slot selection."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Unit tests for chain length, parallel ordering, single-flight order, and fence-overlap slot filling with skip barrier, shared paths and bypass run-alone
# relates: [clutch/drain.py, clutch/tickets.py]
# owner: engine
# verified: 62301251
# hash: 2943ea7b6e2093a08f1a9f4c4cde09c07ccfa216051a6ee64414b19239f8e794

from clutch.drain import SKIP_LIMIT, chain, fill_slots, order_tickets, parallel_order
from clutch.tickets import Frontmatter, GateBypass, Ticket


def ticket(stem, priority="P2", depends=(), before=(), path=None, bypass=False):
    return Ticket(
        stem=stem,
        frontmatter=Frontmatter(
            state="confirmed",
            source="human",
            priority=priority,
            kind="feature",
            gate_bypass=[GateBypass(code="scope_fence", reason="unbounded")] if bypass else [],
        ),
        sections={},
        depends=depends,
        context=(),
        on_demand=(),
        scope_fence=(path or stem,),
        verification=(),
        expected_minutes=20,
        stuck_minutes=40,
        runs_before=before,
    )


def stems(tickets):
    return [t.stem for t in tickets]


def test_chain_diamond_soft_edge_and_cycle():
    a = ticket("a", before=("e",))
    b = ticket("b", depends=("a",))
    c = ticket("c", depends=("a",))
    d = ticket("d", depends=("b", "c"))
    diamond = {t.stem: t for t in (a, b, c, d)}
    assert chain("a", diamond) == 3
    assert chain("d", diamond) == 0
    diamond["e"] = ticket("e")
    assert chain("a", diamond) == 4
    cycle = {t.stem: t for t in (ticket("a", depends=("b",)), ticket("b", depends=("a",)))}
    assert chain("a", cycle) == 1


def test_parallel_priority_chain_and_soft_edges():
    zero = ticket("zero", "P0")
    long = ticket("long", "P1")
    middle = ticket("middle", "P2")
    short = ticket("short", "P1")
    children = [ticket(f"l{i}", depends=("long",)) for i in range(5)]
    children += [ticket(f"m{i}", depends=("middle",)) for i in range(3)]
    unsettled = {t.stem: t for t in [zero, long, middle, short, *children]}
    assert stems(parallel_order([short, middle, long, zero], {}, unsettled)) == ["zero", "long", "short", "middle"]
    x = ticket("x", "P1", before=("y",))
    y = ticket("y", "P0")
    assert stems(parallel_order([y, x], {}, {"x": x, "y": y})) == ["x", "y"]


def test_single_flight_order_is_unchanged():
    a = ticket("a", "P1", before=("z",))
    z = ticket("z", "P0")
    b = ticket("b", "P1")
    c = ticket("c", "P1")
    assert stems(order_tickets([z, c, a, b], {"a": "2", "b": "1"})) == ["b", "a", "z", "c"]


def test_fill_slots_and_selected_overlap():
    a, b, c = (ticket(s) for s in ("a", "b", "c"))
    assert stems(fill_slots([a, b, c], [], 2, [], {"a": 2}, set())[0]) == ["a", "b"]
    dispatch, counts = fill_slots([a, ticket("overlap", path="a"), c], [], 2, [], {"a": 2}, set())
    assert stems(dispatch) == ["a", "c"]
    assert counts == {"overlap": 1}


def test_skips_barrier_and_input_unchanged():
    busy = ticket("busy", path="src")
    blocked = ticket("blocked", path="src/file")
    later = ticket("later", path="docs")
    original = {"other": 2}
    dispatch, counts = fill_slots([blocked, later], [busy], 2, [], original, set())
    assert stems(dispatch) == ["later"]
    assert counts == {"other": 2, "blocked": 1}
    assert original == {"other": 2}
    dispatch, counts = fill_slots([blocked, later], [busy], 2, [], {"blocked": SKIP_LIMIT}, set())
    assert stems(dispatch) == ["later"]
    assert counts == {"blocked": 4}


def test_shared_and_bypass_use_fence_overlap():
    busy = ticket("busy", path="docs")
    allowed = ticket("allowed", path="docs/file")
    bypass = ticket("bypass", path="docs/file", bypass=True)
    dispatch, counts = fill_slots([allowed, bypass], [busy], 2, ["docs"], {}, set())
    assert stems(dispatch) == ["allowed"]
    assert counts == {"bypass": 1}
