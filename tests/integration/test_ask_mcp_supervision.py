# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Checks that the drain-loop, plan-ticket-drain and plan-ticket-serve ask prompts include the MCP-first, CLI-fallback supervision, event-waiting, subagent routing and serve-lifecycle instructions, and that the roadmap operation docs match.
# relates: [clutch/ask.py, clutch/mcp.py]
# owner: engine
# verified: 8a7948cf
# hash: f404fe73163566d7fa4497ada95a24b05ab75f75ef545c2293110920477e4eb3
import re
from pathlib import Path
from types import SimpleNamespace

import pytest

from clutch import ask, mcp


@pytest.fixture(params=("drain-loop", "plan-ticket-drain", "plan-ticket-serve"))
def prompt(request):
    repo = Path("/repo")
    return ask.render(request.param, "", SimpleNamespace(state_dir=repo / ".clutch", ask_notes=None), repo)


def test_mcp_and_waiting(prompt):
    for phrase in (
        "When MCP is present",
        "When MCP is absent",
        "clutch_status",
        "clutch_snapshot",
        "clutch_roadmap_status",
        "clutch_prompt",
        "clutch_ticket_confirm",
        "clutch_ticket_reject",
        "clutch_box_suggest",
        "clutch_box_triage",
        "clutch_box_dismiss",
        "clutch_engine_start",
        "clutch_engine_control",
        "clutch host doctor",
        "clutch provider probe",
        "clutch ticket review",
        "host test suite",
        "clutch roadmap gate",
        "clutch_wait_event(cursor=..., timeout_seconds=300)",
        "clutch view events --once --cursor ... --timeout 300",
        "zero missed events",
        "monitor facility",
        "once at the end of a phase right before the release gate",
        "unless the owner explicitly asks otherwise",
        "roadmap_row",
        "not on every tick" if prompt.startswith("You are the supervising") else "Do not run Suggestion Box triage on every tick",
    ):
        assert phrase in prompt, phrase  # Omitting this operator instruction differs.
    names = set(re.findall(r"\bclutch_[a-z_]+\b", prompt))
    assert names <= set(mcp.TOOLS)  # An unregistered tool would strand the operator.


def test_plan_routing_and_serve():
    repo = Path("/repo")
    config = SimpleNamespace(state_dir=repo / ".clutch", ask_notes=None)
    for kind in ("plan-ticket-drain", "plan-ticket-serve"):
        text = ask.render(kind, "", config, repo)
        for phrase in (
            "Antigravity `invoke_subagent`",
            'Model: "inherit"',
            'never `"flash"`',
            "row authors (`clutch prompt author <stem>`) and phase-closing reviews",
            'use `Model: "flash"` only for running `clutch roadmap gate <release>`',
        ):
            assert phrase in text, phrase  # Missing or weaker routing differs.
    serve = ask.render("plan-ticket-serve", "", config, repo)
    for phrase in ('clutch_engine_start(mode="serve")', "clutch engine serve --detach", 'clutch_engine_control(action="stop")', "clutch engine stop", "clutch_evidence_captures"):
        assert phrase in serve, phrase  # A session-tied lifecycle differs.
    for phrase in ("background-process facility", "drain.out", "clutch engine drain"):
        assert phrase not in serve, phrase  # A drain or session-tied lifecycle differs.


def test_roadmap_operation_docs():
    text = (Path(__file__).resolve().parents[2] / "docs/how-clutch-works.md").read_text()
    section = text.split("### 7.5 Roadmap operation", 1)[1].split("\n### ", 1)[0]
    assert "prefers `clutch_*` MCP tools when present, with CLI fallback" in section
    assert "once at the end of a phase right before the release gate unless the owner explicitly asks otherwise" in section
    assert "pending when its tick starts" not in section


def test_serve_recovers_from_wedging_message():
    repo = Path("/repo")
    serve = ask.render("plan-ticket-serve", "", SimpleNamespace(state_dir=repo / ".clutch", ask_notes=None), repo)
    line = next(line for line in serve.splitlines() if line.startswith("- For a pending message whose cause wedges"))
    # Stopping without triaging and restarting leaves an unattended daemon idle.
    assert line == (
        '- For a pending message whose cause wedges the engine or wastes runs, run `clutch_engine_control(action="stop")` or `clutch engine stop` (the running ticket finishes first), take that message through the no-engine Suggestion Box step as an exception to the phase-end triage cadence, then start serve again with `clutch_engine_start(mode="serve")` or `clutch engine serve --detach`.'
    )
