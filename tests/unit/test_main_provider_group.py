# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test main provider group
# relates: [clutch/__main__.py, clutch/providers.py, clutch/seams.py]
# owner: engine
# verified: 69d790e1
# hash: e82371af3cecb2c813f5dd1857ee079c3c88c4a4bb2d5252f15eb199e5e9ea4a
import argparse

import pytest

from clutch import __main__ as entry
from clutch.providers import ADAPTERS
from clutch.seams import ExecutableNotFound


class MissingExec:
    async def run(self, argv, **kwargs):
        raise ExecutableNotFound(argv[0])


def test_provider_group_parses():
    parser = entry._parser()
    args = parser.parse_args(["provider", "install"])
    assert (args.verb, args.provider_verb, args.providers) == ("provider", "install", [])
    assert parser.parse_args(["provider", "install", "claude", "codex"]).providers == ["claude", "codex"]
    args = parser.parse_args(["provider", "probe"])
    assert (args.provider_verb, args.providers) == ("probe", [])
    assert parser.parse_args(["provider", "probe", "claude"]).providers == ["claude"]
    for argv in (["provider"], ["provider", "install", "--write"], ["provider", "probe", "--all"]):
        with pytest.raises(SystemExit) as exc:
            parser.parse_args(argv)
        assert exc.value.code == 2


def test_old_names_refuse():
    parser = entry._parser()
    top = next(a for a in parser._actions if isinstance(a, argparse._SubParsersAction))
    group = next(a for a in top.choices["provider"]._actions if isinstance(a, argparse._SubParsersAction))
    for name in ("install", "probe"):
        assert name not in top.choices and name in group.choices
        with pytest.raises(SystemExit) as exc:
            parser.parse_args([name])
        assert exc.value.code == 2


def test_install_needs_no_config(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(entry, "SubprocessExec", MissingExec)
    assert entry.main(["provider", "install"], cwd=tmp_path, env={}) == 0
    out, err = capsys.readouterr()
    assert err == ""
    assert [line for line in out.splitlines() if not line.startswith("ollama:")] == [
        (
            f"{name}: absent, installed outside pnpm -- follow clutch/docs/host-{name}.md"
            if adapter.PACKAGE is None
            else f"{name}: absent, package {adapter.PACKAGE} -- run: clutch provider install {name}"
        )
        for name, adapter in ADAPTERS.items()
    ]
    assert list(tmp_path.iterdir()) == []


def test_refusals_name_group(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(entry, "SubprocessExec", MissingExec)
    for argv in (["provider", "probe"], ["provider", "install", "llama"]):
        assert entry.main(argv, cwd=tmp_path, env={}) == 2
        out, err = capsys.readouterr()
        assert out == ""
        assert len(err.splitlines()) == 1 and err.startswith("clutch provider: ")
        if argv[1] == "probe":
            assert "config file not found" in err
        else:
            assert err == f"clutch provider: unknown provider 'llama' -- name one of {', '.join(sorted(ADAPTERS))}\n"
    assert list(tmp_path.iterdir()) == []


def test_install_help_names_workspace_file(capsys):
    with pytest.raises(SystemExit):
        entry._parser().parse_args(["provider", "install", "--help"])
    assert "pnpm-workspace.yaml" in capsys.readouterr().out
