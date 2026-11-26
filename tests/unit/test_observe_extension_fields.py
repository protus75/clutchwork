# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Pins the exact extension snapshot fields from observe.extension_fields and checks that every extension command argv parses with the clutch CLI parser
# relates: [clutch/__main__.py, clutch/observe.py]
# owner: engine
# verified: 69d790e1
# hash: ace3d6296f20bafc7a5e3c4c575a846960e4d14544b926a5c8073b3ff0d76f01
from clutch.observe import extension_fields


def test_extension_fields(tmp_path):
    assert extension_fields(tmp_path) == {
        "root": str(tmp_path.resolve()),
        "commands": {
            "review": ["ticket", "review"],
            "lint": ["ticket", "lint"],
            "run": ["engine", "run"],
            "triage": ["box", "triage"],
            "dismiss": ["box", "dismiss"],
            "serve": ["engine", "serve"],
            "stop": ["engine", "stop"],
            "order": ["ticket", "order"],
            "stats": ["view", "stats", "--tree"],
            "askDiagnose": ["prompt", "diagnose"],
            "askReview": ["prompt", "review"],
            "askDrafts": ["prompt", "drafts"],
            "askDrainLoop": ["prompt", "drain-loop"],
            "askBox": ["prompt", "box"],
        },
        "orderFlags": {"priority": "--priority", "runsBefore": "--runs-before"},
        "providerInstalls": [
            {"label": "Update claude", "detail": "installs @anthropic-ai/claude-code@latest", "argv": ["provider", "install", "claude"]},
            {"label": "Update codex", "detail": "installs @openai/codex@latest", "argv": ["provider", "install", "codex"]},
            {"label": "Update qwen", "detail": "installs @qwen-code/qwen-code@latest", "argv": ["provider", "install", "qwen"]},
            {"label": "Update all providers", "detail": "installs all provider CLIs", "argv": ["provider", "install", "claude", "codex", "qwen"]},
        ],
    }


def test_extension_commands_parse(tmp_path):
    from clutch.__main__ import _parser

    for argv in extension_fields(tmp_path)["commands"].values():
        _parser().parse_known_args([*argv, "some-stem"])
