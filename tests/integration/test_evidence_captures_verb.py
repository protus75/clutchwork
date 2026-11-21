"""Capture command outcomes against real files."""

import json

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
    run(["my-ticket", "--attempt", "0"], 2, message="invalid capture input")
    missing = run(["my-ticket", "--attempt", "2", "--name", "a.txt"], 2, message="no capture")
    path = store.root / "captures/my-ticket/1/a.txt.json"
    pointer = json.loads(path.read_bytes())
    path.write_text('{"schema": "bad"}')
    unreadable = run(["my-ticket", "--attempt", "1", "--name", "a.txt"], 2, message="unreadable capture")
    assert missing != unreadable
    path.write_text(json.dumps(pointer))
    store._blob_path(pointer["blob"]).unlink()
    run(["my-ticket", "--attempt", "1", "--name", "a.txt"], 2, message="unreadable capture")
