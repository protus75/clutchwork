import argparse
from pathlib import Path

import pytest

from clutch import __main__ as entry


def test_coverage_group_parses():
    parser = entry._parser()
    args = parser.parse_args(["coverage", "map"])
    assert (args.verb, args.coverage_verb) == ("coverage", "map")
    args = parser.parse_args(["coverage", "gate"])
    assert (args.gate, args.report, args.command) == (Path("test-gate.toml"), Path("coverage.json"), [])
    args = parser.parse_args(["coverage", "gate", "--gate", "g.toml", "--report", "r.json", "--", "pytest"])
    assert (args.gate, args.report, args.command) == (Path("g.toml"), Path("r.json"), ["--", "pytest"])
    for argv in (["coverage"], ["coverage", "map", "--x"]):
        with pytest.raises(SystemExit) as exc:
            parser.parse_args(argv)
        assert exc.value.code == 2


def test_old_names_refuse():
    parser = entry._parser()
    top = next(a for a in parser._actions if isinstance(a, argparse._SubParsersAction))
    group = next(a for a in top.choices["coverage"]._actions if isinstance(a, argparse._SubParsersAction))
    assert set(group.choices) == {"map", "gate"}
    for name in ("covmap", "covgate"):
        assert name not in top.choices
        with pytest.raises(SystemExit) as exc:
            parser.parse_args([name])
        assert exc.value.code == 2


def test_gate_needs_no_config(tmp_path, capsys):
    assert entry.main(["coverage", "gate"], cwd=tmp_path, env={}) == 2
    out, err = capsys.readouterr()
    assert out == ""
    assert err == "clutch coverage: name the unit-test command after --\n"
    assert list(tmp_path.iterdir()) == []


def test_map_config_error_road(tmp_path, capsys):
    assert entry.main(["coverage", "map"], cwd=tmp_path, env={}) == 2
    out, err = capsys.readouterr()
    assert out == ""
    assert len(err.splitlines()) == 1
    assert err.startswith("clutch coverage: ")
    assert "config file not found" in err
    assert err.rstrip().endswith("-- repair the selected config and retry coverage map")
