# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test admission facts
# relates: [clutch/journal.py, clutch/observe.py, clutch/reconcile.py, clutch/rework.py, clutch/status.py, clutch/tickets.py]
# owner: engine
# verified: 0a308920
# hash: 0d20093efd124afafef1107f4137a4683a606c867a738db3487ee0e17d69ea77
from collections.abc import Iterable
from itertools import product
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from clutch import observe, reconcile, rework, status
from clutch.journal import Event, EventType
from clutch.status import CLOSED, SETTLED, Admission, last_states, reject_queue


# Reference rules copied from status.py before admission facts.
def old_run_admission(stem, events, file_exists, ticket, intake_decision=None, stray=()):
    """Dispatch admission; ticket is the full disk validation, including evidence."""
    from clutch.rework import settled_dependencies
    from clutch.tickets import ticket_path

    if stray:
        return old_intake_stray_admission(stray)
    road = f"fix the ticket, then `engine run {stem}` again"
    for label, decision in (("failed intake", intake_decision), ("is invalid", ticket)):
        if isinstance(decision, list) and decision:
            return Admission("refuse", f"{ticket_path(stem)} {label}: " + "; ".join(f"[{f.code}] {f.message} ({f.paved_road})" for f in decision), road)
    if not file_exists:
        return Admission("refuse", f"{ticket_path(stem)} does not exist", f"author it with `clutch ticket new {stem}`, fill it, then `clutch engine run {stem}`")
    events = tuple(events)
    if last_states(events).get(stem) == "merged" or ticket.frontmatter.state == "merged":
        return Admission("refuse", f"{stem} is already merged", "author follow-up work as a new stem with `ticket new`")
    if ticket.frontmatter.state != "confirmed":
        return Admission("refuse", f"{stem} is `state: {ticket.frontmatter.state}`, not confirmed", f"set `state: confirmed` in {ticket_path(stem)} to dispatch it, or author a new stem")
    if unmerged := [d for d in ticket.depends if d not in settled_dependencies(events)]:
        return Admission("refuse", f"{stem} depends on unmerged {', '.join(unmerged)}", " then ".join(f"`engine run {d}`" for d in unmerged) + f" first, then `engine run {stem}`")
    return Admission("admit")


def old_intake_stray_admission(stray):
    return Admission(
        "refuse",
        f"staged changes outside pending ticket files: {', '.join(stray)}",
        "unstage them; a ticket-plane commit carries only `tickets/<stem>/ticket.md` and regular, non-symlink evidence files for that pending stem",
    )


def old_review_admission(stem, events, file_exists, ticket, intake_decision=None, stray=(), pending=False):
    """Review admission; ticket is validated main text, or claimed pending text."""
    from clutch.tickets import stem_findings, ticket_path

    if findings := stem_findings(stem):
        return Admission("refuse", findings[0].message, findings[0].paved_road)
    if pending and stray:
        return old_intake_stray_admission(stray)
    road = f"fix the ticket and retry `ticket review {stem}`"
    if pending and isinstance(intake_decision, list) and intake_decision:
        return Admission("refuse", f"{ticket_path(stem)} failed intake: " + "; ".join(f.message for f in intake_decision), road)
    if not file_exists:
        return Admission("refuse", f"{ticket_path(stem)} does not exist", f"author the ticket before `ticket review {stem}`")
    if last_states(events).get(stem) in CLOSED:
        return Admission("refuse", f"{stem} is settled or rejected", "author follow-up work as a new ticket")
    if isinstance(ticket, list) and ticket:
        return Admission("refuse", f"{ticket_path(stem)} is invalid: " + "; ".join(f.message for f in ticket), road)
    return Admission("admit")


def old_order_admission(stem, events, file_exists, lock_holder, ticket=None):
    from clutch.reconcile import orphans
    from clutch.tickets import ticket_path

    if not file_exists:
        return Admission("refuse", f"{ticket_path(stem)} does not exist", f"author it with clutch ticket new {stem}")
    events = tuple(events)
    state = last_states(events).get(stem)
    if state == "running" and (stem not in orphans(events) or lock_holder is not None):
        return Admission("refuse", f"{stem} is running; editing a ticket during its run stops it with ticket_changed", "reorder it after the run ends")
    if state in CLOSED:
        return Admission("refuse", f"{stem} is {state}", "author follow-up work as a new ticket")
    if isinstance(ticket, list) and ticket:
        return Admission("refuse", ticket[0].message, ticket[0].paved_road)
    return Admission("admit")


def old_lint_admission(stem, events, file_exists):
    if not file_exists:
        return Admission("refuse", "no ticket file", "create tickets/<stem>/ticket.md with clutch ticket new <stem>")
    if last_states(events).get(stem) in CLOSED:
        return Admission("noop")
    return Admission("admit")


def old_verdict_refusal(events: Iterable[Event], stem: str, kill: bool, draft: bool, interrupted: set[str]) -> tuple[str, str] | None:
    """Apply verdict admission after the interrupted runs have been reaped."""
    history = list(events) + [SimpleNamespace(type=EventType.STATE_TRANSITION, ticket=s, body={"to": "abandoned"}) for s in interrupted]
    last = last_states(history).get(stem)
    if last == "running":
        return f"{stem} is running", "wait for its terminal, then retry"
    if kill:
        if last in SETTLED:
            return f"{stem} is settled", "leave settled work in place"
    elif not draft and stem not in reject_queue(history):
        return f"{stem} is neither a draft nor in the Reject queue", "run `status` to list the Reject queue"
    return None


def old_confirm_admission(events, stem, draft, interrupted):
    refusal = old_verdict_refusal(events, stem, False, draft, interrupted)
    return Admission("refuse", *refusal) if refusal else Admission("admit")


def old_reject_admission(events, stem, draft, interrupted):
    refusal = old_verdict_refusal(events, stem, True, draft, interrupted)
    return Admission("refuse", *refusal) if refusal else Admission("admit")


def transition(stem, target, **body):
    return SimpleNamespace(type=EventType.STATE_TRANSITION, ticket=stem, body={"to": target, **body}, key=None)


def signal(stem, name, **body):
    return SimpleNamespace(type=EventType.SIGNAL, ticket=stem, body={"signal": name, **body}, key=None)


HISTORIES = [
    [],
    [transition("item", "merged")],
    [transition("item", "running")],
    [transition("item", "rejected")],
    [transition("item", "gate_failed", routed="reject_queue")],
    [transition("item", "gate_failed"), signal("item", "reject_arrival")],
    [transition("item", "gate_failed", routed="reject_queue"), signal("item", "reject_verdict")],
    [transition("item", "gate_failed", routed="reject_queue"), transition("item", "merged")],
    [signal("parent", "supersedes", successors=["left", "right"]), transition("left", "merged"), transition("right", "already_satisfied")],
    [signal("parent", "supersedes", successors=["left", "right"]), transition("left", "merged"), transition("right", "running")],
]


@pytest.mark.parametrize("history", HISTORIES)
def test_facts_and_admission_parity(history):
    facts = status.admission_facts(iter(history))
    assert facts.states == last_states(history)
    assert facts.settled == rework.settled_dependencies(history)
    assert facts.orphans == frozenset(reconcile.orphans(history))
    assert facts.reject == frozenset(reject_queue(history))
    for stem in {e.ticket for e in history} | {"absent"}:
        ticket = SimpleNamespace(frontmatter=SimpleNamespace(state="confirmed"), depends=("parent",))
        for kill, draft, interrupted in product((False, True), repeat=3):
            overlay = {stem} if interrupted else set()
            assert status.verdict_refusal(facts, stem, kill, draft, overlay) == old_verdict_refusal(history, stem, kill, draft, overlay)
            assert status.confirm_admission(facts, stem, draft, overlay) == old_confirm_admission(history, stem, draft, overlay)
            assert status.reject_admission(facts, stem, draft, overlay) == old_reject_admission(history, stem, draft, overlay)
        assert status.run_admission(stem, facts, True, ticket) == old_run_admission(stem, history, True, ticket)
        assert status.review_admission(stem, facts, True, ticket) == old_review_admission(stem, history, True, ticket)
        assert status.lint_admission(stem, facts, True) == old_lint_admission(stem, history, True)
        for holder in (None, object()):
            assert status.order_admission(stem, facts, True, holder) == old_order_admission(stem, history, True, holder)


def test_queue_arrival_and_merge():
    assert status.admission_facts(HISTORIES[5]).reject == frozenset({"item"})
    assert status.admission_facts(HISTORIES[7]).reject == frozenset()
    assert "parent" in status.admission_facts(HISTORIES[8]).settled
    assert "parent" not in status.admission_facts(HISTORIES[9]).settled


def test_admissions_do_not_recompute(monkeypatch):
    facts = status.admission_facts([transition("item", "running")])

    def fail(*args):
        raise AssertionError("history recomputed")

    for module, name in ((status, "last_states"), (status, "reject_queue"), (rework, "settled_dependencies"), (reconcile, "orphans")):
        monkeypatch.setattr(module, name, fail)
    ticket = SimpleNamespace(frontmatter=SimpleNamespace(state="confirmed"), depends=())
    non_orphan = status.AdmissionFacts(facts.states, facts.settled, frozenset(), facts.reject)
    assert status.order_admission("item", non_orphan, True, None).outcome == "refuse"
    assert status.run_admission("item", facts, True, ticket).outcome == "admit"
    assert status.review_admission("item", facts, True, ticket).outcome == "admit"
    assert status.order_admission("item", facts, True, None).outcome == "admit"
    assert status.lint_admission("item", facts, True).outcome == "admit"
    assert status.verdict_refusal(facts, "item", False, False, set())[0] == "item is running"
    assert status.confirm_admission(facts, "item", False, set()).outcome == "refuse"
    assert status.reject_admission(facts, "item", False, set()).outcome == "refuse"


def test_menu_shares_facts(monkeypatch):
    root = Path("/fake")
    stems = {"one", "two", "three"}
    monkeypatch.setattr(Path, "is_file", lambda p: True)
    monkeypatch.setattr(Path, "read_text", lambda p: "text")
    monkeypatch.setattr(observe, "_graph", lambda *a: {})
    monkeypatch.setattr(observe, "validate_ticket", lambda *a, **k: object())
    monkeypatch.setattr(observe, "git_output", lambda *a: "text")
    facts = status.admission_facts([transition("one", "running")])
    spy = Mock(wraps=status.admission_facts)
    monkeypatch.setattr(status, "admission_facts", spy)
    git = SimpleNamespace(status_porcelain=AsyncMock(return_value=""))
    ctx = SimpleNamespace(root=root, git=git)
    rows, _, _ = observe.ticket_menu_inputs(ctx, facts, stems, None, set())
    spy.assert_not_called()
    shared = rows["one"]["clutchRun"]["facts"]
    assert shared is facts
    for row in rows.values():
        for inputs in row.values():
            assert inputs["facts"] is shared
            assert "events" not in inputs
