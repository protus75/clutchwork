"""Exercise capture command through the composition root."""

from clutch.__main__ import main
from clutch.evidence.store import EvidenceStore
from clutch.seams import LocalFileSystem
from tests.integration.test_cli import CONFIG


def test_main_captures(tmp_path, capsys):
    (tmp_path / "config.yaml").write_text(CONFIG)
    fs = LocalFileSystem()
    store = EvidenceStore(tmp_path / ".clutch/state", fs, fs.read_bytes, fs.size, lambda text: text)
    assert main(["evidence", "captures", "my-ticket"], cwd=tmp_path) == 0
    assert capsys.readouterr().out == "no captures for my-ticket\n"
    store.put_capture("my-ticket", 1, "a.txt", b"stored text")
    assert main(["evidence", "captures", "my-ticket"], cwd=tmp_path) == 0
    assert capsys.readouterr().out == "1 a.txt\n"
    assert main(["evidence", "captures", "my-ticket", "--attempt", "1", "--name", "a.txt"], cwd=tmp_path) == 0
    assert capsys.readouterr().out == "stored text"
    assert main(["evidence", "captures", "my-ticket", "--name", "a.txt"], cwd=tmp_path) == 2
    assert "requires an attempt" in capsys.readouterr().err
