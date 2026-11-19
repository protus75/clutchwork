"""The parser accepts the checked-in roadmap, not just synthetic tables."""

from pathlib import Path

from clutch.roadmap import choose, parse

ROOT = Path(__file__).resolve().parents[2]


def test_real_roadmap_parses():
    rows = parse((ROOT / "docs/roadmap.md").read_text())
    author = next(row for row in rows if row.number == 90)
    assert (author.stem, author.kind, author.priority) == ("roadmap-author", "feature", "P1")
    choose(rows, states={}, files=set())
