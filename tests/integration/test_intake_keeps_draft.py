# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Tests that intake keeps the authored draft state, that drain waits for `ticket confirm`, and that the author and drafts specs and the authoring guide carry the confirm guidance.
# relates: [clutch/__main__.py, clutch/drain.py, clutch/journal.py, tests/integration/test_cli.py, tests/integration/test_drain.py]
# owner: engine
# verified: ae1a5a3b
# hash: aed2f291a245c8de1c9d9b7b2f2c6fb8f082b981f4baaa34473c4c73116331eb
import asyncio
from pathlib import Path

import pytest

from clutch import __main__ as entry
from clutch.drain import drain
from clutch.journal import EventType
from tests.cli_helpers import ENV, git_out, ticket, write
from tests.integration.test_drain import pause_checkout, root
from tests.integration.test_drain_reentry import NoChild
from tests.integration.test_tickets import VALID, do_intake, repo
from tests.integration.test_tickets import write as write_ticket

pytestmark = pytest.mark.disk_io_skip

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize(("state", "expected"), [("draft", "draft"), (None, "confirmed"), ("confirmed", "confirmed")])
def test_intake_preserves_authored_state(repo, state, expected):
    checkout, git, journal = repo
    text = VALID if state is None else VALID.replace("---\n", f"---\nstate: {state}\n", 1)
    write_ticket(checkout, "human", text)
    do_intake(checkout, git, journal)
    committed = git_out(checkout, "show", "HEAD:tickets/human/ticket.md").split("---", 2)[1]
    assert f"state: {expected}\n" in committed
    assert f"state: {'confirmed' if expected == 'draft' else 'draft'}\n" not in committed
    assert "source: human\n" in committed


@pytest.mark.asyncio
async def test_drain_waits_for_human_confirmation(root):
    write(root, "human", ticket().replace("---\n", "---\nstate: draft\n", 1))
    checkout = pause_checkout(root)
    calls = []

    async def dispatch(item):
        calls.append(item.stem)
        checkout.journal.append(EventType.STATE_TRANSITION, {"to": "merged"}, ticket=item.stem)
        return "merged"

    await drain(checkout, dispatch, reexec=NoChild())
    committed = git_out(root, "show", "HEAD:tickets/human/ticket.md")
    assert "state: draft\n" in committed and "state: confirmed\n" not in committed
    assert "source: human\n" in committed
    assert calls == []
    assert await asyncio.to_thread(entry.main, ["ticket", "confirm", "--yes", "human"], cwd=root, env=ENV, clock=checkout.clock) == 0
    await drain(pause_checkout(root), dispatch, reexec=NoChild())
    assert calls == ["human"]


def test_author_and_drafts_guidance():
    author = (ROOT / "clutch/specs/ask/author.md").read_text().splitlines()
    assert any("clutch ticket confirm" in line and "Run no git verb" in line for line in author)
    assert any("clutch ticket confirm" in line and "Run no git verb" not in line for line in author)
    drafts = (ROOT / "clutch/specs/ask/drafts.md").read_text().splitlines()
    assert any("source" in line and "human" in line and "skipped" in line and "no confirm or reject" in line for line in drafts)
    guide = (ROOT / "clutch/docs/host-authoring.md").read_text().split("## Workflow", 1)[1].split("\n## ", 1)[0]
    assert "clutch ticket confirm" in guide
