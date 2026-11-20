# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test docs verb
# relates: [clutch/__init__.py, clutch/__main__.py, clutch/runner.py]
# owner: engine
# verified: 0a308920
# hash: c3b015bc31cce9ef94dc89bf6688f23a9968b9d83de3da2cd9bd27c5a919efe0
from pathlib import Path
from unittest.mock import Mock

import pytest

import clutch
from clutch import __main__ as cli
from clutch.runner import Refusal


def test_docs_without_config_or_lock(monkeypatch, capsys):
    monkeypatch.setattr(cli, "load_config", Mock(side_effect=AssertionError("config read")))
    monkeypatch.setattr(cli, "Lockfile", Mock(side_effect=AssertionError("lock taken")))
    assert cli.main(["host", "docs"], cwd=Path("/absent-host")) == 0
    lines = capsys.readouterr().out.splitlines()
    directory = Path(clutch.__file__).parent / "docs"
    assert [line.split("  ")[0] for line in lines] == [str(directory / f"host-{name}.md") for name in ("authoring", "running", "contract", "qwen", "gemini", "training")]
    assert all(line.split("  ")[1] for line in lines)


def test_new_guide_paths_without_disk(monkeypatch, capsys):
    fs = Mock()
    monkeypatch.setattr(cli, "LocalFileSystem", lambda: fs)
    monkeypatch.setattr(cli, "template", lambda kind: "skeleton")
    monkeypatch.setattr(cli, "validate_ticket", lambda stem, text, repo: "ticket")
    monkeypatch.setattr(cli, "evidence_findings", lambda ticket, repo: [])
    monkeypatch.setattr(cli, "lint_findings", lambda ticket, repo: [])
    monkeypatch.setattr(Path, "exists", lambda self: False)
    guide = Path(clutch.__file__).parent / "docs" / "host-authoring.md"
    assert cli._new(Path("/host"), "new-ticket") == 0
    assert f"read the ticket authoring guide before filling sections: {guide}" in capsys.readouterr().out.splitlines()
    fs.write.assert_called_once_with(Path("/host/tickets/new-ticket/ticket.md"), b"skeleton")
    monkeypatch.setattr(Path, "exists", lambda self: True)
    with pytest.raises(Refusal) as error:
        cli._new(Path("/host"), "new-ticket")
    assert f"read {guide}, then edit it in place, or pick a new stem" in str(error.value)
