"""Priority, chain length, and soft edges in parallel ordering."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Unit tests that parallel ordering ranks priority before chain length, chain before age within a priority, and that runs-before soft edges override priority
# relates: [clutch/drain.py, clutch/tickets.py]
# owner: engine
# verified: 5a232ea2
# hash: 9f5851f103c758b020d519292e278976a55f0f15b34dbd16b327152359e69d07

from clutch.drain import parallel_order
from clutch.tickets import Frontmatter, Ticket


def ticket(stem, priority="P2", depends=(), before=()):
    return Ticket(
        stem=stem,
        frontmatter=Frontmatter(state="confirmed", source="human", priority=priority, kind="feature"),
        sections={},
        depends=depends,
        context=(),
        on_demand=(),
        scope_fence=(stem,),
        verification=(),
        expected_minutes=20,
        stuck_minutes=40,
        runs_before=before,
    )


def test_priority_precedes_chain():
    p1 = ticket("p1_lone", "P1")
    p2 = ticket("p2_long")
    children = [ticket(f"child{i}", depends=(p2.stem,)) for i in range(3)]
    unsettled = {t.stem: t for t in (p1, p2, *children)}
    assert [t.stem for t in parallel_order([p2, p1], {}, unsettled)] == ["p1_lone", "p2_long"]


def test_chain_precedes_age_within_priority():
    short = ticket("p1_short", "P1")
    long = ticket("p1_long", "P1")
    children = [ticket(f"child{i}", depends=(long.stem,)) for i in range(2)]
    unsettled = {t.stem: t for t in (short, long, *children)}
    assert [t.stem for t in parallel_order([short, long], {short.stem: "1", long.stem: "2"}, unsettled)] == ["p1_long", "p1_short"]


def test_soft_edge_overrides_priority():
    first = ticket("p2_first", before=("p1_next",))
    next_ticket = ticket("p1_next", "P1")
    unsettled = {t.stem: t for t in (first, next_ticket)}
    assert [t.stem for t in parallel_order([next_ticket, first], {}, unsettled)] == ["p2_first", "p1_next"]
