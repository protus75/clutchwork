"""The production terminal path publishes reviewed edits or lifts refused proposals."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: The production terminal path publishes reviewed edits or lifts refused proposals.
# relates: [clutch/audit.py, clutch/caps.py, clutch/drain.py, clutch/journal.py, clutch/status.py, tests/approval.py]
# owner: engine
# verified: 96e46658
# hash: 83d99795a00370ff28fb54f403685f47d35bcc9547321cad06c02613c5822091

import asyncio
import json

from clutch.audit import audit_journal
from clutch.caps import consume, supervise_draws
from clutch.drain import awaiting_operator, parked_blob, reofferable
from clutch.journal import EventType
from clutch.status import reject_queue
from tests.approval import approve
from tests.integration.test_requisition_gate import dispatch, reply, setup
from tests.integration.test_stages import implement_reply

PREMISE = implement_reply("premise_failed", [{"code": "premise", "path": "tests/x.py", "message": "missing fence", "paved_road": "reword scope"}])


def test_premise_terminal_is_edited_reviewed_and_kept(tmp_path):
    root, checkout, llm, writer = setup(tmp_path, [])
    original = (root / "tickets/gate/ticket.md").read_text()
    proposal = original.replace("In: thing. Out: the rest.", "In: implement thing. Out: the rest.").strip()
    assert "In: implement thing. Out: the rest." in proposal  # Wrong fixture: an unchanged proposal would exercise refusal.
    llm.script.extend([PREMISE, json.dumps({"action": "update", "tickets": [{"stem": "gate", "ticket": proposal}]}), reply("approve")])
    approve(root, "gate", checkout.clock)

    async def exercise():
        assert await dispatch(root, checkout, writer) == "premise_failed"
        sha = await checkout.git.rev_parse(root, "HEAD:tickets/gate/ticket.md")
        assert await checkout.git._run(root, "show", "HEAD:tickets/gate/ticket.md") == proposal  # Wrong: review without publishing exact proposal.
        assert (await checkout.git._run(root, "log", "-1", "--format=%s", "--", "tickets/gate/ticket.md")).strip() == "clutch(gate): rework"
        return sha

    sha = asyncio.run(exercise())
    assert [r.surface for r in llm.requests] == ["implement", "rework", "requisition_review"]
    assert '"trigger": "premise_bounce cap spent"' in llm.requests[1].rendered  # Wrong: run ordinary Rework without supervisor restrictions.
    events = checkout.journal.read()
    terminal = next(i for i, e in enumerate(events) if e.type == EventType.STATE_TRANSITION and e.body.get("to") == "premise_failed")
    assert events[terminal + 1].type == EventType.CAP_CONSUMED and events[terminal + 1].body == {"cap": "supervise", "ticket_sha": sha}
    assert events[terminal + 2].body == {"signal": "reject_verdict", "verdict": "keep", "actor": "supervisor", "ticket_sha": sha}  # Wrong: keep before terminal or against old blob.
    assert "gate" not in reject_queue(events) and awaiting_operator(events, "gate", checkout.config.caps) is False
    assert reofferable(events, "gate", checkout.config.caps) is True and parked_blob(events, "gate") != sha  # Wrong: retain spent caps or unchanged content park.


def test_refused_edit_escalates_with_rework_md(tmp_path):
    root, checkout, llm, writer = setup(tmp_path, [])
    original = (root / "tickets/gate/ticket.md").read_text()
    proposal = original.replace("`thing()` returns ok.", "A different supervisor goal.")
    assert proposal != original
    llm.script.extend([PREMISE, json.dumps({"action": "update", "tickets": [{"stem": "gate", "ticket": proposal}]})])
    approve(root, "gate", checkout.clock)
    asyncio.run(dispatch(root, checkout, writer))
    assert [r.surface for r in llm.requests] == ["implement", "rework"]  # Wrong: send forbidden Goal edit to review.

    async def committed():
        assert await checkout.git._run(root, "show", "HEAD:tickets/gate/ticket.md") == original  # Wrong: publish forbidden edit.
        assert (await checkout.git._run(root, "log", "-1", "--format=%s", "--", "tickets/gate/rework.md")).strip() == "clutch(gate): rework-proposal"
        return await checkout.git._run(root, "show", "HEAD:tickets/gate/rework.md")

    report = asyncio.run(committed())
    assert "supervise_edit" in report and "A different supervisor goal." in report  # Wrong: discard refused proposal.
    events = checkout.journal.read()
    assert "gate" in reject_queue(events) and supervise_draws(events, "gate") == 0
    assert not any(e.body.get("actor") == "supervisor" for e in events)  # Wrong: keep a refused update.
    assert audit_journal(checkout.journal) == []  # Wrong: effect after terminal causes abandoned second terminal.


def test_spent_supervise_cap_leaves_the_stem_for_the_operator(tmp_path):
    root, checkout, llm, writer = setup(tmp_path, [PREMISE])
    approve(root, "gate", checkout.clock)
    for sha in ("first-edit", "second-edit"):
        consume(checkout.journal, "gate", "supervise", sha)
    asyncio.run(dispatch(root, checkout, writer))
    assert [r.surface for r in llm.requests] == ["implement"]  # Wrong: permit a third supervisor call.
    assert not (root / "tickets/gate/rework.md").exists() and "gate" in reject_queue(checkout.journal.read())
