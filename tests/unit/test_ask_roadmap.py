# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test ask roadmap
# relates: [clutch/__main__.py]
# owner: clutch/__main__.py
# verified: 0a308920
# hash: 2e10b7e8316c1a63ed23df4454804bcaa85825062bc05612db5f6089147ab717
from pathlib import Path
from types import SimpleNamespace

import pytest

from clutch import __main__ as entry


def test_roadmap_dispatch_and_help(monkeypatch, tmp_path, capsys):
    config = SimpleNamespace(state_dir=tmp_path / "state", ask_notes=None)
    monkeypatch.setattr(entry, "load_config", lambda *a, **k: config)
    monkeypatch.setattr(entry, "child_env", lambda *a: {})
    monkeypatch.setattr(Path, "read_text", lambda self: "body" if self.parent.name == "type" else "facet=${facet}")
    assert entry.main(["prompt", "roadmap"], cwd=tmp_path) == 0  # Treating roadmap as a ticket prompt refuses.
    assert capsys.readouterr().out == "facet=body"  # Omitting either resource changes the output.
    assert entry.main(["prompt", "roadmap", "extra"], cwd=tmp_path) == 2  # Accepting an operand must refuse.
    error = capsys.readouterr().err
    assert "roadmap takes no stem" in error and "clutch prompt roadmap with no stems" in error  # Both the refusal and remedy must identify the problem.
    with pytest.raises(SystemExit) as result:
        entry.main(["prompt", "roadmap", "--help"], cwd=tmp_path)
    assert result.value.code == 0  # Help must exit successfully.
    help_text = capsys.readouterr().out
    assert "clutch prompt roadmap\n" in help_text  # An operand in the example is wrong.
