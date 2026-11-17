import argparse
import re
from pathlib import Path

import pytest

from clutch import __main__ as entry
from clutch import ask
from clutch.config import load_config
from tests.integration.test_config import VALID


@pytest.fixture
def prompts(tmp_path):
    (tmp_path / "config.yaml").write_text(VALID.replace("state_dir: .clutch", "state_dir: custom/state"))
    config = load_config(None, cwd=tmp_path)
    return {kind: ask.render(kind, "" if kind == "plan-ticket-drain" else "unique-stem", config, tmp_path) for kind in ("plan-ticket-drain", "author", "review")}


def test_plan_ticket_drain_prompt_content(prompts):
    text = prompts["plan-ticket-drain"]
    for phrase in (
        "docs/roadmap.md",
        "standing delegation",
        "conduct files",
        "explicit override",
        "the engine authored",
        "clutch doctor",
        "clutch probe",
        "clutch release --minor",
        "never twice",
        "clutch prompt drain-loop",
        "clutch prompt diagnose",
        "clutch prompt drafts",
        "clutch prompt box",
        "clutch prompt running",
        "clutch confirm --yes",
        "clutch reject --yes",
        "clutch suggest",
        "No person is in the loop",
        "Proposed",
        "different model family",
        "counted in runs",
        "Never push",
        "while a ticket runs",
        "the tick it appears",
        "roadmap_row",
        "clutch roadmap author --ahead",
        "drift failure",
        "clutch prompt author",
        "clutch prompt review",
        "never hold",
        "clutch roadmap status",
        "clutch stop",
        "roadmap_drive",
        "custom/state/engine.log",
        "custom/state/drain.out",
        "P1 row",
        "never a Suggestion Box message",
        "before the last of them merges",
        "run once",
        "next: none",
        "Still open:",
    ):
        assert phrase in text, phrase
    assert text.index("conduct files") < text.index("clutch doctor") < text.index("clutch probe") < text.index("clutch prompt drain-loop")
    assert text.index("standing delegation") < text.index("clutch confirm --yes")
    assert "Let the driver author" not in text
    assert "Hand-author only when the driver cannot" not in text
    assert not text.startswith("/loop")


def test_author_prompt_content(prompts):
    text = prompts["author"]
    for phrase in (
        "`unique-stem`",
        "tickets/unique-stem/ticket.md",
        "clutch new unique-stem --kind",
        "--evidence",
        "clutch docs",
        "clutch lint unique-stem",
        "clutch review unique-stem",
        "clutch status",
        "clutch suggest",
        "one write",
        "Fence closure",
        "confirmed, unmerged",
        "Depends on",
        "Runs before",
        "at most 3",
        "6 rounds",
        "approved",
        "skipped",
        "review_stuck",
        "failed",
    ):
        assert phrase in text, phrase
    assert text.index("clutch new unique-stem") < text.index("clutch lint unique-stem") < text.index("clutch review unique-stem")


def test_review_prompt_is_audit(prompts):
    text = prompts["review"]
    for phrase in (
        "`unique-stem`",
        "tickets/unique-stem/ticket.md",
        "clutch docs",
        "clutch status",
        "confirmed, unmerged",
        "either merge order",
        "blocking",
        "minor",
        "Scope fence",
        "Verification",
        '"Recommendation"',
        "wait for me to say go",
    ):
        assert phrase in text, phrase


def test_prompts_carry_no_session_facts(prompts):
    for text in prompts.values():
        for phrase in ("${", "./dev.py", "uv run", "/home/", ".claude", "bash", "fungo", "claude", "codex", "qwen", "ollama", "gemini"):
            assert phrase not in text.lower(), phrase


def test_prompts_name_only_existing_verbs(prompts):
    parser = entry._parser()
    commands = next(a.choices for a in parser._actions if isinstance(a, argparse._SubParsersAction))
    roadmap = next(a.choices for a in commands["roadmap"]._actions if isinstance(a, argparse._SubParsersAction))
    for text in prompts.values():
        matches = re.findall(r"`clutch ([a-z-]+)(?: ([a-z-]+))?", text)
        assert matches
        for first, second in matches:
            assert first in commands
            if first == "prompt" and second:
                assert second in ask.KINDS
            if first == "roadmap" and second:
                assert second in roadmap


def test_docs_list_new_prompt_kinds():
    running = Path("clutch/docs/host-running.md").read_text()
    row = next(line for line in running.splitlines() if line.startswith("| `prompt` |"))
    assert "plan-ticket-drain" in row and "author" in row
    lines = Path("docs/how-clutch-works.md").read_text().splitlines()
    assert any(line.startswith("| `prompt author <stem>` |") for line in lines)
    assert any(line.startswith("| `prompt plan-ticket-drain` |") for line in lines)
    assert any(line.startswith("| `prompt <diagnose") and "audits" in line for line in lines)
