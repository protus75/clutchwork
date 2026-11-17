"""Keep the host run guide's verb table aligned with the CLI."""

import argparse
import re
from pathlib import Path

from clutch.__main__ import _parser


def test_verb_table_matches_parser():
    doc = (Path(__file__).resolve().parents[2] / "clutch/docs/host-running.md").read_text()
    rows = re.findall(r"^\| `([^`]+)` \|", doc, re.M)
    subcommands = next(action for action in _parser()._actions if isinstance(action, argparse._SubParsersAction))
    assert len(rows) == len(set(rows))
    paths = [row.split() for row in rows]
    assert {path[0] for path in paths} == set(subcommands.choices)
    for path in paths:
        assert len(path) in (1, 2)
        if len(path) == 2:
            children = next(a for a in subcommands.choices[path[0]]._actions if isinstance(a, argparse._SubParsersAction))
            assert path[1] in children.choices
    for group in {path[0] for path in paths if len(path) == 2}:
        children = next(a for a in subcommands.choices[group]._actions if isinstance(a, argparse._SubParsersAction))
        assert {path[1] for path in paths if len(path) == 2 and path[0] == group} == set(children.choices)
