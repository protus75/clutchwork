# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Tests that intake scoped to named stems, and the named ticket verbs, leave other pending or staged tickets untouched.
# relates: [clutch/__main__.py, clutch/journal.py, clutch/llm.py, clutch/seams.py, clutch/tickets.py, tests/integration/test_cli.py]
# owner: engine
# verified: ae1a5a3b
# hash: bda2afc1482315807df8fe101cc5df469d60115f799cb1667c2b58c2d2151cca
import asyncio

import pytest

from clutch.__main__ import main
from clutch.journal import EventType, Journal
from clutch.llm import FakeLLM
from clutch.seams import LocalFileSystem
from clutch.tickets import intake
from tests.cli_helpers import ENV, Clock, Stages, git_out, ticket, write
from tests.integration.test_drain import make_root
from tests.integration.test_review_command import reply
from tests.integration.test_tickets import VALID, repo

pytestmark = pytest.mark.disk_io_skip


def test_scoped_intake_leaves_invalid_staged_ticket(repo):
    root, git, journal = repo
    write(root, "alpha", VALID)
    write(root, "beta", VALID.replace("priority: P2", "priority: invalid"))
    asyncio.run(git.add(root, ["tickets/beta/ticket.md"]))
    result = asyncio.run(intake(root, git, journal, LocalFileSystem(), stems={"alpha"}))
    assert result.committed == ("alpha",)
    assert "beta" not in result.refused
    assert asyncio.run(git._run(root, "diff", "--cached", "--name-only")).splitlines() == ["tickets/beta/ticket.md"]
    assert asyncio.run(git._run(root, "show", "--name-only", "--format=", "HEAD")).splitlines() == ["tickets/alpha/ticket.md"]


@pytest.mark.parametrize("verb", ["review", "run", "confirm", "reject"])
def test_named_verbs_leave_other_pending_ticket(tmp_path, monkeypatch, verb):
    root = make_root(tmp_path)
    draft = ticket().replace("---\n", "---\nstate: draft\n", 1)
    write(root, "alpha", draft)
    write(root, "beta", draft)
    beta = (root / "tickets/beta/ticket.md").read_bytes()
    monkeypatch.setattr("clutch.__main__.ProviderLLM", lambda *args, **kwargs: FakeLLM([reply("approve")]))
    args = [*(["ticket"] if verb in {"review", "confirm", "reject"} else ["engine"] if verb == "run" else []), verb, "alpha"] + (["--yes"] if verb in {"confirm", "reject"} else [])
    assert main(args, cwd=root, env=ENV, clock=Clock(), pipeline=Stages()) == (2 if verb == "run" else 0)
    subjects = git_out(root, "log", "--format=%s").splitlines()
    assert "clutch(alpha): ticket" in subjects
    assert "clutch(beta): ticket" not in subjects
    assert (root / "tickets/beta/ticket.md").read_bytes() == beta
    assert git_out(root, "status", "--porcelain", "--", "tickets/beta/").strip()
    events = Journal(root / ".clutch/state", Clock()).read()
    assert not any(e.type == EventType.SIGNAL and e.body.get("signal") == "ticket_intake" and e.ticket == "beta" for e in events)
