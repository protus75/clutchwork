"""Recent Steps keeps rendering unknown and known step kinds."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Checks through a node harness that the extension's Recent Steps view draws an unknown step kind as a warning row and keeps the icon and text for a known kind
# relates: [tests/vscode_step_unknown.js, clutch/observe.py, tests/integration/conftest.py]
# owner: engine
# verified: 5b8a60b2
# hash: d5a14028f4dd0de6fca3ad07539f78e6f440b5527d8da66b700618fb6710392a

import json
import subprocess
from pathlib import Path

HARNESS = Path(__file__).parents[1] / "vscode_step_unknown.js"


def draw(kind):
    result = subprocess.run(["node", str(HARNESS), kind], capture_output=True, text=True, check=True, timeout=10)
    return json.loads(result.stdout)


def test_unknown_kind_warns():
    assert draw("not_a_kind") == {
        "icon": "warning",
        "description": "cannot draw the clutch snapshot: unknown step kind not_a_kind",
    }


def test_known_kind_keeps_icon_and_text():
    assert draw("check_ok") == {"icon": "checklist", "description": "A check completed"}
