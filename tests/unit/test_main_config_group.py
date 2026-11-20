# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test main config group
# relates: [clutch/__main__.py, clutch/seams.py]
# owner: engine
# verified: 0a308920
# hash: 857213abd5d6810f37c22440004eb6facc8f30008c611ebd664cb2697f026121
import argparse
from pathlib import Path

import pytest

from clutch import __main__ as entry
from clutch.seams import ExecutableNotFound


def test_config_group_parses():
    parser = entry._parser()
    args = parser.parse_args(["config", "init"])
    assert (args.verb, args.config_verb, args.write, args.config) == ("config", "init", False, None)
    assert parser.parse_args(["config", "init", "--write"]).write is True
    assert parser.parse_args(["config", "update"]).config_verb == "update"
    args = parser.parse_args(["--config", "host.yaml", "config", "migrate"])
    assert (args.config_verb, args.config) == ("migrate", Path("host.yaml"))
    for argv in (["config"], ["config", "update", "--write"], ["config", "migrate", "--write"]):
        with pytest.raises(SystemExit) as exc:
            parser.parse_args(argv)
        assert exc.value.code == 2


def test_old_names_refuse():
    parser = entry._parser()
    top = next(a for a in parser._actions if isinstance(a, argparse._SubParsersAction))
    group = next(a for a in top.choices["config"]._actions if isinstance(a, argparse._SubParsersAction))
    for old, name in zip(("init-config", "update-config", "migrate-config"), ("init", "update", "migrate"), strict=True):
        assert old not in top.choices
        assert name in group.choices
        with pytest.raises(SystemExit) as exc:
            parser.parse_args([old])
        assert exc.value.code == 2


def test_refusals_name_group(tmp_path, monkeypatch, capsys):
    class MissingExec:
        async def run(self, argv, **kwargs):
            raise ExecutableNotFound(argv[0])

    monkeypatch.setattr(entry, "SubprocessExec", MissingExec)
    for verb, message in (("update", "config file not found"), ("migrate", "cannot read config file"), ("init", "no provider CLI found -- ")):
        assert entry.main(["config", verb], cwd=tmp_path, env={}) == 2
        output = capsys.readouterr()
        assert output.out == ""
        assert len(output.err.splitlines()) == 1
        assert output.err.startswith("clutch config: ")
        assert message in output.err
        if verb == "migrate":
            assert "config file not found" not in output.err
        if verb == "init":
            assert output.err.startswith("clutch config: no provider CLI found -- ")
    assert list(tmp_path.iterdir()) == []
