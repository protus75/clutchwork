# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test observe extension fields
# relates: [clutch/__main__.py, clutch/observe.py]
# owner: engine
# verified: 9a610809
# hash: 41c0e35420f711f08b86dbb49d39c74e702ddfd9723bb80a6a828cd5eaa12534
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
    }


def test_extension_commands_parse(tmp_path):
    from clutch.__main__ import _parser

    for argv in extension_fields(tmp_path)["commands"].values():
        _parser().parse_known_args([*argv, "some-stem"])
