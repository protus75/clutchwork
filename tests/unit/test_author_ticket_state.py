# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Checks that the author reads ticket state from frontmatter, detects rejection from the file or the journal, and lists only open tickets
# relates: [clutch/author.py, clutch/journal.py]
# owner: engine
# verified: c015c627
# hash: 1eedc868a4cff2d31387c97aa21ea8d2d7b9c7ed8b8b5700874de09458cee3bc
import asyncio
from types import SimpleNamespace

from clutch.author import is_rejected, list_open_tickets, ticket_state
from clutch.journal import EventType
from tests.git_fake import GitFake


def test_ticket_state():
    assert ticket_state("---\nstate: rejected\npriority: P1\n---\n\n## Goal / Why\nx\n") == "rejected"
    assert ticket_state("## Goal / Why\nx\n") is None
    assert ticket_state("---\n: : [\n---\nbody") is None
    assert ticket_state("---\npriority: P1\n---\nbody") is None


def test_rejection_and_open_listing(tmp_path):
    texts = {
        stem: f"---\nstate: {state}\n---\n\n## Goal / Why\n{stem} goal\n"
        for stem, state in {
            "live": "confirmed",
            "rej": "rejected",
            "jrej": "confirmed",
            "sat": "confirmed",
        }.items()
    }
    for stem, text in texts.items():
        path = tmp_path / "tickets" / stem / "ticket.md"
        path.parent.mkdir(parents=True)
        path.write_text(text)

    async def rev_parse(repo, ref):
        return "committed"

    async def run(repo, command, ref):
        return texts[ref.split("/")[1]]

    events = [SimpleNamespace(type=EventType.STATE_TRANSITION, ticket=stem, body={"to": state}) for stem, state in [("jrej", "rejected"), ("sat", "already_satisfied")]]
    checkout = SimpleNamespace(repo=tmp_path, git=GitFake(rev_parse=rev_parse, _run=run), journal=SimpleNamespace(read=lambda: events))
    for stem, expected in [("rej", True), ("jrej", True), ("live", False), ("sat", False)]:
        assert asyncio.run(is_rejected(checkout, stem)) is expected
    assert asyncio.run(list_open_tickets(checkout)) == "live: live goal"
