from clutch.observe import extension_fields


def test_extension_fields(tmp_path):
    assert extension_fields(tmp_path) == {
        "root": str(tmp_path.resolve()),
        "commands": {
            "review": ["review"],
            "lint": ["lint"],
            "run": ["run"],
            "triage": ["triage"],
            "dismiss": ["dismiss"],
            "serve": ["serve"],
            "stop": ["stop"],
            "order": ["order"],
            "stats": ["stats", "--tree"],
            "askDiagnose": ["prompt", "diagnose"],
            "askReview": ["prompt", "review"],
            "askDrafts": ["prompt", "drafts"],
            "askDrainLoop": ["prompt", "drain-loop"],
            "askBox": ["prompt", "box"],
        },
        "orderFlags": {"priority": "--priority", "runsBefore": "--runs-before"},
    }
