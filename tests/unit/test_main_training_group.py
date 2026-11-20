import pytest

from clutch import __main__ as entry


def test_parser():
    parser = entry._parser()
    args = parser.parse_args(["training", "export", "--out", "dest", "--kinds", "preference", "--holdout", "50"])
    assert (args.training_verb, args.kinds, args.holdout) == ("export", ["preference"], 50)
    for argv in (
        ["training", "export"],
        ["training", "export", "--out", "x", "--kinds", "review"],
        ["training", "export", "--out", "x", "--holdout", "101"],
        ["training", "export", "--out", "x", "--holdout", "-1"],
    ):
        with pytest.raises(SystemExit):
            parser.parse_args(argv)
