# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Checks that the plan-ticket-drain and plan-ticket-serve prompts rendered by clutch/ask.py include the same session-handoff, events-monitor, and once-per-release roadmap-gate rules.
# relates: [clutch/ask.py]
# owner: clutch/ask.py
# verified: c3fcaf81
# hash: 4d1eb85681d81f3040e7bdb0855e0ff629e8ca106b6245fb9fea5e9411dbcef5
from pathlib import Path
from types import SimpleNamespace

import pytest

from clutch import ask


def render(kind):
    repo = Path("/repo")
    config = SimpleNamespace(state_dir=repo / ".clutch", ask_notes=None)
    return ask.render(kind, "", config, repo)


@pytest.mark.parametrize("kind", ["plan-ticket-drain", "plan-ticket-serve"])
def test_session_handoff(kind):
    text = render(kind)
    supervising = text.index("Supervising:")
    tick = text.index("- Priority is the order:", supervising)
    log = text.index("- Keep a log the next tick reads", tick)
    closing = text.index("Closing each phase:", log)
    handoff = text[log:closing]
    for phrase in (
        "Before the before-start checks finish, read the HANDOFF section at the end of the log if present, then read the live queue",
        "20 merged tickets since this session began, counted from `clutch view status`, never wall-clock time",
        "finish the current tick, write a HANDOFF section at the end of the log, report, and stop",
        "decisions made and why, open threads, verdicts about to be executed, and instructions the owner gave in chat that no ticket holds",
        "never copies ticket stems, statuses, order, or engine state",
        "The next session reads those from `clutch view snapshot` and `clutch view status`",
        f"`clutch prompt {kind}` — Read the HANDOFF section at the end of the log first",
    ):
        assert phrase in handoff, phrase

    monitor = text[tick:log]
    for phrase in (
        "Arm `clutch view events` under your agent's monitor facility once with the longest timeout the facility allows",
        "re-arm only when it expires",
        "never write a loop that polls `clutch view status`, `clutch prompt drafts`, or a process list on a timer",
    ):
        assert phrase in monitor, phrase

    gate = text[closing:].splitlines()[1]
    for phrase in (
        "with nothing running or confirmed unrun",
        "`clutch roadmap gate <release>` through one Sonnet subagent once per release",
        "returns only pass or fail, the first failing command and its output tail",
        "Never rerun a gate with an existing result unless a merge landed since that result",
    ):
        assert phrase in gate, phrase


def test_shared_session_rules_match():
    drain = render("plan-ticket-drain")
    serve = render("plan-ticket-serve")

    def rules(text, kind):
        log = next(line for line in text.splitlines() if line.startswith("- Keep a log the next tick reads"))
        gate = next(line for line in text.splitlines() if line.startswith("- Once the queue has drained"))
        monitor = text.split("Arm `clutch view events`", 1)[1].split(" Start new authoring", 1)[0]
        return log.replace(kind, "plan-ticket-MODE"), gate, monitor

    assert rules(drain, "plan-ticket-drain") == rules(serve, "plan-ticket-serve")
