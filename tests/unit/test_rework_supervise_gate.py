import pytest

from clutch.rework import ReworkReply, TicketProposal, supervise_findings

ORIGINAL = """---
state: confirmed
---
## Context
- a.py
## Goal / Why
Build it.
## Scope in / Scope out
In: a.
## Scope fence
- a.py
## Acceptance criteria
1. First.
2. Second.
""".strip()


def update(text):
    return ReworkReply(action="update", tickets=[TicketProposal(stem="original", ticket=text)])


def test_split_is_refused():
    reply = ReworkReply(action="split", tickets=[TicketProposal(stem="one", ticket="one"), TicketProposal(stem="two", ticket="two")])
    [finding] = supervise_findings("original", ORIGINAL, reply)
    assert (finding.code, finding.message, finding.path) == ("supervise_edit", "a supervisor edit cannot split the ticket", "tickets/original/ticket.md")
    assert "`clutch ticket confirm original`" in finding.paved_road and "`clutch ticket reject original`" in finding.paved_road


@pytest.mark.parametrize(
    ("proposal", "messages"),
    [
        (ORIGINAL, ["the proposal does not change the ticket text"]),
        (ORIGINAL.replace("Build it.", "Build another."), ["the proposal changes `## Goal / Why`"]),
        (ORIGINAL.replace("2. Second.", ""), ["the proposal drops acceptance criteria (1 of 2 remain)"]),
        (ORIGINAL.replace("Build it.\n", "Build it.\n\n"), []),
    ],
)
def test_update_refusals(proposal, messages):
    assert [f.message for f in supervise_findings("original", ORIGINAL, update(proposal))] == messages


def test_allowed_edits_pass():
    text = (
        ORIGINAL.replace("- a.py\n## Goal", "- a.py\n- b.py\n## Goal")
        .replace("In: a.", "In: a and b.")
        .replace("- a.py\n## Acceptance", "- a.py\n- b.py\n## Acceptance")
        .replace("2. Second.", "2. Reworded second.")
    )
    assert supervise_findings("original", ORIGINAL, update(text)) == []
    assert supervise_findings("original", ORIGINAL, ReworkReply(action="escalate", tickets=[])) == []
