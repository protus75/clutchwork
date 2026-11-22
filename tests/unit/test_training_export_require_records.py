"""Exercise the training export record requirement through the CLI."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Unit tests for `training export --require-records`: exit 2 after writing when a requested kind is empty, unrequested kinds ignored, and the flag's parser default and help text
# relates: [clutch/__main__.py, clutch/git.py, clutch/training.py, tests/config_fixture.py]
# owner: clutch/training.py
# verified: fd6afe46
# hash: 10d973d3f3a2e0fc000eec5e0134ca29476c331d9605004e96be4e61a6fe6f55

from clutch import __main__ as cli
from clutch import training
from clutch.git import Git
from tests.config_fixture import build_config


def test_empty_export_requires_records(tmp_path, capsys, monkeypatch):
    (tmp_path / "config.yaml").write_text(build_config() + "\ntraining_data: {enabled: true}\n")

    async def merged_tickets(self, directory):
        return []

    monkeypatch.setattr(Git, "merged_tickets", merged_tickets)
    (tmp_path / "out").mkdir()
    (tmp_path / "out" / "sft.jsonl").write_text("stale")
    argv = ["training", "export", "--out", str(tmp_path / "out")]
    # A refusal must follow the report and the file write, while the default remains successful.
    assert cli.main(argv + ["--require-records"], cwd=tmp_path) == 2
    captured = capsys.readouterr()
    assert "implement: 0, preference: 0, review: 0, diagnosis: 0" in captured.out
    assert all(kind in captured.err for kind in ("implement", "preference", "review", "diagnosis"))
    assert "run more tickets with training_data.enabled, or drop the kind from --kinds" in captured.err
    assert (tmp_path / "out" / "sft.jsonl").read_text() == ""
    assert cli.main(argv, cwd=tmp_path) == 0
    assert capsys.readouterr().err == ""


def test_requested_counts(tmp_path, capsys, monkeypatch):
    (tmp_path / "config.yaml").write_text(build_config() + "\ntraining_data: {enabled: true}\n")
    counts = dict.fromkeys(("implement", "preference", "review", "diagnosis", "ticket", "conflict", "triage", "dropped", "skipped", "heldout"), 0)
    counts["ticket"] = 3

    async def render(*args, **kwargs):
        return {}, counts

    monkeypatch.setattr(training, "render", render)
    argv = ["training", "export", "--out", str(tmp_path / "out"), "--kinds", "ticket", "triage", "--require-records"]
    # An unrequested empty kind must not affect the result, and only the empty requested kind is named.
    assert cli.main(argv, cwd=tmp_path) == 2
    captured = capsys.readouterr()
    assert "triage" in captured.err and "ticket" not in captured.err.split("run more tickets")[0]
    counts["triage"] = 2
    assert cli.main(argv, cwd=tmp_path) == 0
    assert capsys.readouterr().err == ""


def test_parser_and_help():
    parser = cli._parser()
    argv = ["training", "export", "--out", "out"]
    # A default-on flag or an ignored flag must fail independently.
    assert parser.parse_args(argv).require_records is False
    assert parser.parse_args(argv + ["--require-records"]).require_records is True
    export = parser._subparsers._group_actions[0].choices["training"]._subparsers._group_actions[0].choices["export"]
    help_text = export.format_help()
    assert "--require-records" in help_text and "2 when disabled, refused" in help_text and "requested kind empty" in help_text
