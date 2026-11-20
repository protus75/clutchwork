"""The parser accepts the checked-in roadmap, not just synthetic tables."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: The parser accepts the checked-in roadmap, not just synthetic tables.
# relates: [clutch/roadmap.py]
# owner: clutch/roadmap.py
# verified: 96e46658
# hash: dfe2e32a064591f4601ab405d06f9de03d9f7f6a1b5c9abe4ae31e1a9c43024f

from pathlib import Path

from clutch.roadmap import choose, parse

ROOT = Path(__file__).resolve().parents[2]


def test_real_roadmap_parses():
    rows = parse((ROOT / "docs/roadmap.md").read_text())
    author = next(row for row in rows if row.number == 90)
    assert (author.stem, author.kind, author.priority) == ("roadmap-author", "feature", "P1")
    choose(rows, states={}, files=set())
