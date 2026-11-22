# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Unit tests for the `clutch prompt host` and `clutch prompt list` verbs: rendering, refusal exit codes, invalid host prompt files and a missing prompts_dir
# relates: [clutch/__main__.py, tests/config_helpers.py]
# owner: engine
# verified: f74aec75
# hash: 39d7d11ea5cd5ec5b11fabbfff2a5a51e78031a0694c2b9758b9a51225071800
from clutch.__main__ import main
from tests.config_helpers import VALID


def test_host_and_list(tmp_path, capsys):
    (tmp_path / "config.yaml").write_text(VALID + "prompts_dir: prompts\n")
    prompts = tmp_path / "prompts"
    prompts.mkdir()
    (prompts / "notes.md").write_text("---\ndescription: Notes\ntakes: stem\n---\n$stem $ticket")
    ticket = tmp_path / "tickets/example/ticket.md"
    ticket.parent.mkdir(parents=True)
    ticket.write_text("ticket")
    assert main(["prompt", "host", "notes", "example"], cwd=tmp_path) == 0
    assert capsys.readouterr().out == "example tickets/example/ticket.md"
    assert main(["prompt", "list"], cwd=tmp_path) == 0
    assert "prompt host notes\tstem\tNotes" in capsys.readouterr().out
    for args in (["notes"], ["missing"], ["notes", "absent"]):
        assert main(["prompt", "host", *args], cwd=tmp_path) == 2
        out = capsys.readouterr()
        assert not out.out and " -- " in out.err
    (prompts / "bad.md").write_text("bad")
    assert main(["prompt", "list"], cwd=tmp_path) == 2
    assert "bad.md" in capsys.readouterr().err
    assert main(["prompt", "host", "bad"], cwd=tmp_path) == 2
    assert "bad.md" in capsys.readouterr().err
    (tmp_path / "config.yaml").write_text(VALID)
    assert main(["prompt", "host", "notes", "example"], cwd=tmp_path) == 2
    out = capsys.readouterr()
    assert not out.out and "prompts_dir" in out.err
