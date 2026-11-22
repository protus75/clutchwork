"""Check the extension against the snapshot's step-kind vocabulary."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Checks that the VS Code extension gives every snapshot step kind a distinct icon, and that recent step events use only that step-kind vocabulary.
# relates: [clutch/observe.py]
# owner: clutch/observe.py
# verified: d32c32ad
# hash: b4cb21ccce68c99ce1d99fdcb275e136aa9a54db1136bb1bca8115ac6b74616c

import json
import subprocess
from pathlib import Path

import pytest

from clutch.observe import PHASE_NAMES, STEP_KINDS, STEP_NAMES, recent_steps

pytestmark = pytest.mark.disk_io_skip

HARNESS = Path(__file__).parents[1] / "vscode_step_icons.js"


def test_every_step_has_a_distinct_icon():
    result = subprocess.run(
        ["node", str(HARNESS), json.dumps(list(STEP_KINDS))],
        capture_output=True,
        text=True,
        check=True,
        timeout=10,
    )
    icons = json.loads(result.stdout)
    assert set(icons) == set(STEP_KINDS)
    assert all(icons.values())
    by_step = {}
    for kind, step in STEP_KINDS.items():
        by_step.setdefault(step, set()).add(icons[kind])
    assert all(len(ids) == 1 for ids in by_step.values())
    assert len({next(iter(ids)) for ids in by_step.values()}) == len(by_step)


def test_recent_step_events_use_the_vocabulary():
    log = []
    for category, names in (("stage", STEP_NAMES), ("phase", PHASE_NAMES)):
        for name in names:
            for suffix, outcome in (("start", None), ("end", "ok"), ("end", "failed")):
                log.append({"event": f"{category}_{suffix}", "surface" if category == "stage" else "phase": name, "outcome": outcome, "ts": f"{len(log):04d}"})
    rows = recent_steps(None, log, len(log))
    expected = {f"{name}_{suffix}" for name in (*STEP_NAMES, *PHASE_NAMES) for suffix in ("start", "ok", "failed")}
    assert {row["kind"] for row in rows} == expected
    assert expected <= STEP_KINDS.keys()
