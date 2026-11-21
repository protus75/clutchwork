"""Closed evidence command vocabulary and complete command help."""

import pytest

from clutch.__main__ import _parser, _subparsers


def test_evidence_commands():
    parser = _parser()
    group = _subparsers(parser).choices["evidence"]
    commands = _subparsers(group).choices
    # Rules out missing verbs and accidental extra verbs.
    assert set(commands) == {"show", "schema", "renormalize", "coverage", "captures"}
    for argv, expected in [
        (["show", "a/b"], ("show", "a/b")),
        (["schema", "start"], ("schema", "start")),
        (["schema", "end"], ("schema", "end")),
        (["schema", "event"], ("schema", "event")),
        (["renormalize", "--prefix", "llm/a"], ("renormalize", "llm/a")),
        (["renormalize"], ("renormalize", "")),
        (["coverage"], ("coverage", None)),
        (["captures", "my-ticket", "--attempt", "2", "--name", "a/b.txt"], ("captures", None)),
    ]:
        args = parser.parse_args(["evidence", *argv])
        # Rules out losing positional arguments or prefix/default wiring.
        assert (args.evidence_verb, getattr(args, "call_key", getattr(args, "record", getattr(args, "prefix", None)))) == expected
    for name, command in commands.items():
        for field in ("Reads:", "Writes:", "Lock:", "Exit codes:"):
            # Rules out bypassing _command's complete help contract.
            assert field in command.description
        assert f"clutch evidence {name}" in command.epilog


@pytest.mark.parametrize("argv", [["schema", "bogus"], ["bogus"], ["show"], [], ["captures"], ["captures", "my-ticket", "--attempt", "x"]])
def test_invalid_evidence_command(argv):
    # Rules out accepting an open record/verb vocabulary or an absent required key.
    with pytest.raises(SystemExit) as exc:
        _parser().parse_args(["evidence", *argv])
    assert exc.value.code == 2
