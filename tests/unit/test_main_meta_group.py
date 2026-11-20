from clutch.__main__ import _parser


def test_meta_commands_and_help():
    parser = _parser()
    assert parser.parse_args(["meta", "refresh", "tests/a.py"]).meta_verb == "refresh"
    assert parser.parse_args(["meta", "check"]).meta_verb == "check"
    assert "meta refresh" in parser.format_help()
    assert "meta check" in parser.format_help()
