# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Checks that the snapshot prompt picker lists engine prompts, valid host prompts with their argv and takes, invalid host files without argv, and stem and box arguments that the CLI parser accepts
# relates: [clutch/__main__.py, clutch/ask.py, clutch/config.py, clutch/observe.py, tests/config_fixture.py]
# owner: engine
# verified: 290c435a
# hash: b850ba569173da9b20a8d55872b53c25a1e976750f16cbe726e6b2c1c4284fa9
from clutch import ask
from clutch.__main__ import _parser
from clutch.config import load_config
from clutch.observe import prompt_pick
from tests.config_fixture import build_config


def test_prompt_catalog_and_arguments(tmp_path):
    prompts = tmp_path / "prompts"
    prompts.mkdir()
    (prompts / "notes.md").write_text("---\ndescription: Notes for a ticket\ntakes: stem\n---\n$stem\n")
    bad = prompts / "bad.md"
    bad.write_text("missing frontmatter")
    config_path = tmp_path / "config.yaml"
    config_path.write_text(build_config() + "prompts_dir: prompts\n")
    config = load_config(config_path, cwd=tmp_path)

    result = prompt_pick(config, tmp_path, ["b", "a"], ["box-1"])
    entries = result["promptPick"]
    assert [entry["label"] for entry in entries] == [*ask.KINDS, "host notes", str(bad)]
    assert [entry["detail"] for entry in entries[: len(ask.KINDS)]] == [ask.DESCRIPTIONS[kind] for kind in ask.KINDS]
    assert entries[-2] == {"label": "host notes", "detail": "Notes for a ticket", "argv": ["prompt", "host", "notes"], "takes": "stem"}
    assert "argv" not in entries[-1]
    assert "missing YAML frontmatter" in entries[-1]["detail"]
    assert result["promptArgs"] == {"stem": ["b", "a"], "box": ["box-1"]}
    for entry in entries[:-1]:
        _parser().parse_args(entry["argv"] + (["example"] if entry["takes"] in ("stem", "box") else []))
