"""Exercise capture command through the composition root."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Tests that `evidence captures` lists stored captures, prints a named capture, and refuses `--name` without `--attempt`.
# relates: [clutch/__main__.py, clutch/evidence/store.py, clutch/seams.py, tests/integration/test_cli.py]
# owner: engine
# verified: ae1a5a3b
# hash: 190612dd06bc8ba0f2e56d7ecf49f43d306af7661c7b3b3b989af77ae3b76481

from clutch.__main__ import main
from clutch.evidence.store import EvidenceStore
from clutch.seams import LocalFileSystem
from tests.cli_helpers import CONFIG


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
