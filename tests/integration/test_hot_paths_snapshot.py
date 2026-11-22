# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Tests that snapshot rows show a Shared fence detail only for open tickets that share fenced paths, never for closed or rejected ones
# relates: [clutch/journal.py, clutch/observe.py, tests/integration/test_cli.py, tests/integration/test_drain.py, tests/integration/test_retro.py]
# owner: engine
# verified: ff6ac88d
# hash: f5c8f8d2bfa299eae38556586c42f0dd14a6047cc286a4606ea543b00bc86dc4
import pytest

from clutch import observe
from clutch.journal import EventType
from tests.cli_helpers import ENV
from tests.drain_helpers import commit_ticket, confirmed
from tests.misc_helpers import rig

pytestmark = pytest.mark.disk_io_skip


def test_snapshot_shared_fences_exclude_closed_tickets(tmp_path):
    c, _, _, _ = rig(tmp_path)
    shared = confirmed().replace("- clutch/thing.py\n\n## Acceptance", "- open.py\n\n## Acceptance")
    commit_ticket(c.repo, "open", shared)
    ctx = observe.Context(c.repo, c.config.state_dir, c.repo / "config.yaml", None, c.git, ENV)
    lone = observe.snapshot(ctx)
    assert not [d for d in lone["rows"][0]["detail"] if d["heading"] == "Shared fence"]
    commit_ticket(c.repo, "open-two", shared)
    commit_ticket(c.repo, "lone", confirmed().replace("- clutch/thing.py\n\n## Acceptance", "- lone.py\n\n## Acceptance"))
    commit_ticket(c.repo, "closed", shared)
    commit_ticket(c.repo, "rejected", shared.replace("state: confirmed", "state: rejected"))
    c.journal.append(EventType.STATE_TRANSITION, {"to": "merged"}, ticket="closed")
    snap = observe.snapshot(ctx)
    assert "hotPaths" not in snap and "hotPathsHelp" not in snap
    rows = {r["stem"]: r for r in snap["rows"]}
    assert [d for d in rows["open"]["detail"] if d["heading"] == "Shared fence"] == [{"heading": "Shared fence", "text": "open.py (also: open-two)"}]
    assert [d for d in rows["open-two"]["detail"] if d["heading"] == "Shared fence"] == [{"heading": "Shared fence", "text": "open.py (also: open)"}]
    assert not [d for d in rows["lone"]["detail"] if d["heading"] == "Shared fence"]
    assert not [d for d in rows["closed"]["detail"] if d["heading"] == "Shared fence"]
    assert "rejected" not in rows
