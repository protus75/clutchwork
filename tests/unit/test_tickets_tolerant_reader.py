# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test tickets tolerant reader
# relates: [clutch/__main__.py, clutch/observe.py, clutch/stats.py, clutch/tickets.py]
# owner: engine
# verified: 9a610809
# hash: 3285641acd29120483cd4c98e45eca92e09ffe032ecf673f623cde36d646bebb
import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from clutch import __main__ as entry
from clutch import observe, stats, tickets

TEXT = "---\nkind: chore\nstate: confirmed\n---\n## Depends on\n- `alpha`\n- beta\n## Time budget\n- expected: 20m\n- stuck: 40m\n"


def test_valid_ticket():
    result = tickets.read_tolerant(TEXT)
    assert result.frontmatter["kind"] == "chore"
    assert result.depends == ("alpha", "beta")
    assert result.expected_minutes == 20


def test_invalid_ticket_reads_what_parses(tmp_path):
    text = TEXT.replace("kind: chore", "kind: chore\nunknown: value")
    with pytest.raises(tickets.TicketInvalid):
        tickets.parse_ticket("item", text, tmp_path)
    result = tickets.read_tolerant(text)
    assert result.frontmatter["state"] == "confirmed"
    assert result.depends == ("alpha", "beta")
    invalid = tickets.read_tolerant(text.replace("state: confirmed", "state: ["))
    assert invalid.frontmatter == {}
    assert invalid.depends == ("alpha", "beta")
    assert invalid.expected_minutes == 20
    assert tickets.read_tolerant("## Depends on\n- none\n").depends == ()


def test_never_raises():
    empty = tickets.TolerantTicket({}, (), None)
    assert tickets.read_tolerant("") == empty
    assert tickets.read_tolerant("---\n- item\n---\n") == empty
    result = tickets.read_tolerant("## Depends on\n- gamma\n")
    assert result.frontmatter == {}
    assert result.depends == ("gamma",)
    assert tickets.read_tolerant("---\nx: " + "[" * 2000 + "]" * 2000 + "\n---\n").frontmatter == {}
    assert tickets.read_tolerant("## Time budget\n- expected: " + "9" * 5000 + "m\n").expected_minutes is None


def test_observe_readers_delegate(tmp_path):
    path = tmp_path / "ticket.md"
    path.write_text(TEXT)
    assert observe.frontmatter(path) == tickets.read_tolerant(TEXT).frontmatter
    assert observe.depends(path) == list(tickets.read_tolerant(TEXT).depends)
    assert observe.frontmatter(tmp_path / "missing") == {}


def test_stats_reads_kind_from_invalid_ticket(tmp_path, monkeypatch):
    for stem, kind in (("first", "bug"), ("second", "nonsense")):
        path = tmp_path / "tickets" / stem / "ticket.md"
        path.parent.mkdir(parents=True)
        path.write_text(f"---\nkind: {kind}\nunknown: value\n---\n")
    events = [SimpleNamespace(ticket=stem, type=None) for stem in ("first", "second")]
    captured = {}
    monkeypatch.setattr(stats, "project_stats", lambda events, kinds, checks, **kw: captured.update(kinds))
    asyncio.run(entry._stats(SimpleNamespace(repo=tmp_path), events, datetime(2026, 1, 1, tzinfo=UTC), "1d"))
    assert captured == {"first": "bug"}
