"""Carried reproducer for lint reading the main journal from a worktree."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Carried reproducer for lint reading the main journal from a worktree.
# relates: [clutch/__main__.py, clutch/journal.py, tests/integration/test_cli.py, tests/integration/test_lint_verb.py]
# owner: engine
# verified: d7719818
# hash: 4b3bebae206f66fef30735cba1094e52010607e17f6fa127cdc024d9bcf18527

import contextlib
import io
import json
import sys
import tempfile
import traceback
from pathlib import Path


def main() -> int:
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        from clutch.__main__ import main as clutch_main
        from clutch.journal import EventType
        from tests.integration.test_cli import ENV, Clock, journal, root, ticket, write
        from tests.integration.test_lint_verb import git

        with tempfile.TemporaryDirectory() as directory:
            repo = root.__wrapped__(Path(directory))
            write(repo, "merged", "old invalid grammar\n")
            write(repo, "active", ticket().replace("priority: P2", "state: confirmed\nsource: human\npriority: P2"))
            git(repo, "add", "--", "tickets")
            git(repo, "commit", "-m", "tickets")
            journal(repo).append(EventType.STATE_TRANSITION, {"to": "merged"}, ticket="merged")
            worktree = Path(directory) / "worktree"
            git(repo, "worktree", "add", "--detach", str(worktree))
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                result = clutch_main(["ticket", "lint"], cwd=worktree, env=ENV, clock=Clock())
            text = output.getvalue()
            if result == 0 and text == "lint: 1/1 tickets valid\n":
                outcome, code = "pass", 0
            elif result == 1 and "tickets/merged/ticket.md:" in text:
                outcome, code = "defect", 1
            else:
                raise RuntimeError(f"unexpected lint result {result}: {text!r}")
    except Exception:
        traceback.print_exc(file=sys.stderr)
        outcome, code = "error", 2
    print(json.dumps({"regression_result": outcome}))
    return code


if __name__ == "__main__":
    sys.exit(main())
