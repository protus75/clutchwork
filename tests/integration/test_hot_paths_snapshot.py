from clutch import observe
from clutch.journal import EventType
from tests.integration.test_cli import ENV
from tests.integration.test_drain import commit_ticket, confirmed
from tests.integration.test_retro import rig


def test_snapshot_hot_paths_excludes_closed_tickets(tmp_path):
    c, _, _, _ = rig(tmp_path)
    commit_ticket(c.repo, "open", confirmed().replace("- clutch/thing.py\n\n## Acceptance", "- open.py\n\n## Acceptance"))
    ctx = observe.Context(c.repo, c.config.state_dir, c.repo / "config.yaml", None, c.git, ENV)
    assert observe.snapshot(ctx)["hotPaths"] == []
    commit_ticket(c.repo, "open-two", confirmed().replace("- clutch/thing.py\n\n## Acceptance", "- open.py\n\n## Acceptance"))
    commit_ticket(c.repo, "closed", confirmed().replace("- clutch/thing.py\n\n## Acceptance", "- open.py\n\n## Acceptance"))
    commit_ticket(c.repo, "rejected", confirmed().replace("state: confirmed", "state: rejected").replace("- clutch/thing.py\n\n## Acceptance", "- open.py\n\n## Acceptance"))
    c.journal.append(EventType.STATE_TRANSITION, {"to": "merged"}, ticket="closed")
    snap = observe.snapshot(ctx)
    assert snap["hotPathsHelp"] in snap["help"]
    assert snap["hotPaths"] == [{"path": "open.py", "count": 2}]
