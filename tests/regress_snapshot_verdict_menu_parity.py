"""Detect a queued ticket whose Reject menu disagrees with verdict admission."""

import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from clutch import observe
from clutch.box import Box
from tests.unit.test_menu_admission import fake_snapshot_inputs


def main() -> None:
    root = Path("/fake")
    ctx = observe.Context(root, root / "state", root / "config.yaml", None, None, None)
    ticket = SimpleNamespace(stem="queued", frontmatter=SimpleNamespace(priority="P1", state="confirmed"), depends=(), runs_before=(), sections={})
    with (
        patch.object(observe, "journal", return_value=[]),
        patch.object(observe, "journal_facts", lambda state, history: __import__("clutch.status", fromlist=["admission_facts"]).admission_facts(history)),
        patch.object(observe, "load_tickets", return_value=({"queued": ticket}, {})),
        patch.object(observe, "held", lambda history, blobs, candidates: set()),
        patch.object(observe, "operator_holds", lambda ctx, history, candidates: set()),
        patch.object(observe, "running_stems", return_value=[]),
        patch.object(observe, "ticket_menu_inputs", fake_snapshot_inputs),
        patch.object(observe, "uncommitted_tickets", return_value=(set(), set())),
        patch.object(observe, "committed_ticket_shas", return_value={"queued": "sha"}),
        patch.object(observe, "commits", return_value={}),
        patch.object(observe, "lock_holder", return_value=None),
        patch.object(observe, "lock_display", return_value=("", None)),
        patch.object(Path, "exists", return_value=False),
        patch.object(Box, "messages", return_value=[]),
    ):
        menu = observe.snapshot(ctx)["rows"][0]["menu"]
    result = "pass" if menu["clutchReject"] == "on" else "defect"
    print(json.dumps({"regression_result": result}))
    raise SystemExit(0 if result == "pass" else 1)


if __name__ == "__main__":
    main()
