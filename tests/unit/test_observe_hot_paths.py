from clutch.observe import _hot_paths
from clutch.tickets import Frontmatter, Ticket


def ticket(stem, *paths):
    return Ticket(stem, Frontmatter(state="confirmed", source="human", priority="P1", kind="feature"), {}, (), (), (), paths, (), 1, 2)


def test_counts_order_and_distinct_entries():
    tickets = [ticket("one", "c.py", "a.py", "a.py/", "b.py"), ticket("two", "b.py", "a.py"), ticket("three", "a.py")]
    assert _hot_paths(tickets) == [{"path": "a.py", "count": 3}, {"path": "b.py", "count": 2}]


def test_outbox_and_top_ten():
    paths = [f"file-{n:02}.py" for n in reversed(range(12))]
    rows = _hot_paths([ticket("work", "tickets/work", "tickets/work/ticket.md", "alone.py", *paths), ticket("other", "tickets/work", *paths)])
    assert rows == [{"path": f"file-{n:02}.py", "count": 2} for n in range(10)]
    assert _hot_paths([ticket("one", "one.py"), ticket("two", "two.py")]) == []
    assert _hot_paths([ticket("work", "tickets/work", "tickets/work/ticket.md"), ticket("other", "tickets/work")]) == []
