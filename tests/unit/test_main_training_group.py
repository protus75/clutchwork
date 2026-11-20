from pathlib import Path

import pytest

from clutch import __main__ as entry


def test_parser():
    parser = entry._parser()
    args = parser.parse_args(["training", "export", "--out", "dest", "--kinds", "preference", "--holdout", "50"])
    assert (args.training_verb, args.kinds, args.holdout) == ("export", ["preference"], 50)
    assert parser.parse_args(["training", "export", "--out", "x", "--kinds", "ticket"]).kinds == ["ticket"]
    assert parser.parse_args(["training", "export", "--out", "x", "--kinds", "conflict"]).kinds == ["conflict"]
    for argv in (
        ["training", "export"],
        ["training", "export", "--out", "x", "--kinds", "bogus"],
        ["training", "export", "--out", "x", "--since", "2026-13-45"],
        ["training", "export", "--out", "x", "--holdout", "101"],
        ["training", "export", "--out", "x", "--holdout", "-1"],
    ):
        with pytest.raises(SystemExit):
            parser.parse_args(argv)


def test_new_options():
    parser = entry._parser()
    args = parser.parse_args(["training", "export", "--out", "x", "--kinds", "implement", "preference", "review", "diagnosis", "--since", "2026-11-10"])
    assert args.kinds == ["implement", "preference", "review", "diagnosis"]
    assert args.since == "2026-11-10"
    assert parser.parse_args(["training", "export", "--out", "x"]).kinds == args.kinds
    export = parser._subparsers._group_actions[0].choices["training"]._subparsers._group_actions[0].choices["export"]
    assert "--since" in export.format_help() and "conflict" in export.format_help()


def test_eval_parser():
    args = entry._parser().parse_args(["training", "eval", "--route", "medium/review", "--holdout", "h.txt"])
    # Rules out losing the eval verb, route or typed holdout path during parsing.
    assert (args.training_verb, args.route, args.holdout) == ("eval", "medium/review", Path("h.txt"))


@pytest.mark.parametrize("route", ["medium/triage", "review", "bogus/review"])
def test_eval_bad_route(route):
    # Rules out accepting unsupported surfaces, missing tiers or unknown tiers.
    with pytest.raises(SystemExit):
        entry._parser().parse_args(["training", "eval", "--route", route, "--holdout", "h.txt"])
