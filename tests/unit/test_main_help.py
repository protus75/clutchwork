# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test main help
# relates: [clutch/__main__.py, clutch/ask.py]
# owner: engine
# verified: a5584821
# hash: f8c1193b54d608ad7c67dd3fb7115731bc9eb390328216408b19b716f1a356a8
import argparse
import shlex

import pytest

from clutch import ask
from clutch.__main__ import _command, _parser, main


def children(parser):
    return next((a for a in parser._actions if isinstance(a, argparse._SubParsersAction)), None)


def summaries(action):
    return {a.dest: a.help for a in action._choices_actions}


def check_examples(parser, path):
    assert parser.description and parser.description.strip()
    lines = (parser.epilog or "").splitlines()
    assert "Examples:" in lines
    examples = [line.strip() for line in lines[lines.index("Examples:") + 1 :] if line.strip().startswith("clutch ")]
    assert any(line == "clutch " + path or line.startswith("clutch " + path + " ") for line in examples)
    for example in examples:
        try:
            _parser().parse_args(shlex.split(example)[1:])
        except SystemExit as exc:
            assert exc.code == 0


def test_commands_have_description_and_examples():
    top = children(_parser())
    for name, parser in top.choices.items():
        assert summaries(top)[name].strip()
        group = children(parser)
        if group:
            check_examples(parser, name)
            for subname, subparser in group.choices.items():
                check_examples(subparser, f"{name} {subname}")
        elif name == "help":
            check_examples(parser, name)


def test_prompt_group_matches_kinds():
    parser = _parser()
    assert set(children(children(parser).choices["prompt"]).choices) == set(ask.KINDS)
    args = parser.parse_args(["prompt", "box", "a", "b"])
    assert (args.kind, args.stems) == ("box", ["a", "b"])
    assert parser.parse_args(["prompt", "review"]).stems == []


def invoke(argv, tmp_path, capsys):
    try:
        result = main(argv, cwd=tmp_path)
    except SystemExit as exc:
        result = exc.code
    output = capsys.readouterr()
    return result, output.out, output.err


@pytest.mark.parametrize("path", [("roadmap", "merged"), ("prompt", "diagnose"), ("roadmap",), ("ticket", "order")])
def test_help_forms_agree(path, tmp_path, capsys):
    results = [invoke(argv, tmp_path, capsys) for argv in (["help", *path], ["--help", *path], ["-h", *path], [*path, "--help"])]
    assert all(code == 0 and not err for code, _, err in results)
    assert len({out for _, out, _ in results}) == 1
    assert results[0][1].startswith("usage: clutch " + " ".join(path))


def test_top_level_lists_groups(tmp_path, capsys):
    results = [invoke([arg], tmp_path, capsys) for arg in ("help", "--help", "-h")]
    assert all(code == 0 and not err for code, _, err in results)
    assert len({out for _, out, _ in results}) == 1
    output = " ".join(results[0][1].split())
    top = children(_parser())
    for name, summary in summaries(top).items():
        assert output.count(f"{name} {summary}") == 1
        group = children(top.choices[name])
        if group:
            for subname, subsummary in summaries(group).items():
                assert output.count(f"{name} {subname} {subsummary}") == 1


@pytest.mark.parametrize("argv", [["help", "nosuch"], ["--help", "roadmap", "nosuch"]])
def test_unknown_command_refuses(argv, tmp_path, capsys):
    code, out, err = invoke(argv, tmp_path, capsys)
    assert code == 2
    assert out == ""
    assert err.startswith("clutch help: ") and " -- " in err


@pytest.mark.parametrize("missing", ["summary", "does", "reads", "writes", "lock", "exits", "examples"])
def test_command_helper_requires_every_field(missing):
    fields = dict(summary="summary", does="does", reads="reads", writes="writes", lock="lock", exits="exits", examples=["clutch example"])
    del fields[missing]
    with pytest.raises(TypeError):
        _command(argparse.ArgumentParser().add_subparsers(), "example", **fields)


@pytest.mark.parametrize(("verb", "lock"), [("refresh", "Commit lock only."), ("fill", "Writer lock."), ("check", "None.")])
def test_meta_lock_help(verb, lock, tmp_path, capsys):
    code, out, err = invoke(["help", "meta", verb], tmp_path, capsys)
    assert code == 0
    assert not err
    assert f"Lock: {lock}" in out
