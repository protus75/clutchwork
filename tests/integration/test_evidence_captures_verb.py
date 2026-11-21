"""Capture command outcomes against real files."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Verify capture command outcomes and help.
# relates: [clutch/__main__.py, clutch/evidence/store.py, clutch/seams.py, tests/integration/test_cli.py]
# owner: engine
# verified: 8373ae09
# hash: 8fff9a19e8e02f8e8ae33dc6617946c818d99f66b038ed281ef1699ab564144a

import json

import pytest

from clutch.__main__ import main
from clutch.evidence.store import EvidenceStore
from clutch.seams import LocalFileSystem
from tests.integration.test_cli import CONFIG


def test_capture_outcomes_are_read_only(tmp_path, capsys):
    (tmp_path / "config.yaml").write_text(CONFIG)
    fs = LocalFileSystem()
    store = EvidenceStore(tmp_path / ".clutch/state", fs, fs.read_bytes, fs.size, lambda text: text)

    def run(args, code, output=None, message=None):
        before = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
        assert main(["evidence", "captures", *args], cwd=tmp_path) == code
        result = capsys.readouterr()
        assert {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()} == before
        assert not (store.root.parent / "journal").exists()
        if output is not None:
            assert result.out == output
        if message:
            assert result.err.startswith("clutch evidence: " + message)
            assert " -- " in result.err and "clutch evidence captures" in result.err and "Traceback" not in result.err
        return result.err

    run(["my-ticket"], 0, "no captures for my-ticket\n")
    store.put_capture("my-ticket", 1, "a.txt", b"hello")
    run(["my-ticket"], 0, "1 a.txt\n")
    run(["my-ticket", "--attempt", "1", "--name", "a.txt"], 0, "hello")
    run(["my-ticket", "--name", "a.txt"], 2, message="capture name")
    run(["Bad Stem"], 2, message="invalid capture input")
    run(["my-ticket", "--attempt", "-1"], 2, message="invalid capture input")
    run(["my-ticket", "--attempt", "0"], 0, "no captures for my-ticket\n")
    missing = run(["my-ticket", "--attempt", "2", "--name", "a.txt"], 2, message="no capture")
    path = store.root / "captures/my-ticket/1/a.txt.json"
    pointer = json.loads(path.read_bytes())
    path.write_text('{"schema": "bad"}')
    unreadable = run(["my-ticket", "--attempt", "1", "--name", "a.txt"], 2, message="unreadable capture")
    assert missing != unreadable
    path.write_text(json.dumps(pointer))
    store._blob_path(pointer["blob"]).unlink()
    run(["my-ticket", "--attempt", "1", "--name", "a.txt"], 2, message="unreadable capture")


def test_capture_help(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["evidence", "captures", "--help"])
    assert exc.value.code == 0
    output = capsys.readouterr().out
    assert "run-" in output
    assert "attempt 0" in output
