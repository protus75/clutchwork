# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test main meta group
# relates: [clutch/__main__.py]
# owner: clutch/__main__.py
# verified: 0a308920
# hash: 5a1b2121d5d7014315be5a6dd7cc18cd13164cfcef889bbb50658d32da51fa25
from clutch.__main__ import _parser


def test_meta_commands_and_help():
    parser = _parser()
    assert parser.parse_args(["meta", "refresh", "tests/a.py"]).meta_verb == "refresh"
    assert parser.parse_args(["meta", "check"]).meta_verb == "check"
    assert parser.parse_args(["meta", "fill"]).meta_verb == "fill"
    assert "meta fill" in parser.format_help()
    assert "meta refresh" in parser.format_help()
    assert "meta check" in parser.format_help()
