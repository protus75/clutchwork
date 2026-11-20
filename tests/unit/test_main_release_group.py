# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test main release group
# relates: [clutch/__main__.py]
# owner: clutch/__main__.py
# verified: 0a308920
# hash: 39c2692db99dbb37bfdd139675dd74cf8b8f65df42157c81364ad5194083fd92
import argparse

import pytest

from clutch import __main__ as entry


def test_release_group_parses():
    parser = entry._parser()
    args = parser.parse_args(["release", "bump", "--minor"])
    assert (args.verb, args.release_verb, args.part) == ("release", "bump", "minor")
    assert parser.parse_args(["release", "bump", "--patch"]).part == "patch"
    assert parser.parse_args(["release", "publish"]).release_verb == "publish"
    for argv in (["release"], ["release", "bump"], ["release", "bump", "--minor", "--patch"], ["release", "bump", "--major"], ["release", "publish", "--minor"]):
        with pytest.raises(SystemExit) as exc:
            parser.parse_args(argv)
        assert exc.value.code == 2


def test_old_names_refuse():
    parser = entry._parser()
    top = next(a for a in parser._actions if isinstance(a, argparse._SubParsersAction))
    group = next(a for a in top.choices["release"]._actions if isinstance(a, argparse._SubParsersAction))
    assert "publish" not in top.choices
    assert set(group.choices) == {"bump", "publish"}
    for argv in (["publish"], ["release", "--minor"], ["release", "--patch"]):
        with pytest.raises(SystemExit) as exc:
            parser.parse_args(argv)
        assert exc.value.code == 2


def test_refusals_name_group(tmp_path, capsys):
    for argv in (["release", "bump", "--minor"], ["release", "publish"]):
        assert entry.main(argv, cwd=tmp_path, env={}) == 2
        out, err = capsys.readouterr()
        assert out == ""
        assert len(err.splitlines()) == 1 and err.startswith("clutch release: ")
        assert "config file not found" in err
    assert list(tmp_path.iterdir()) == []
