# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Checks the plan-ticket-drain, author, review, drain-loop and running prompts carry required phrases, no session facts and only existing verbs, and that the docs list the prompt kinds
# relates: [clutch/__main__.py, clutch/ask.py, clutch/config.py, tests/integration/test_config.py]
# owner: engine
# verified: 38957300
# hash: 51ea80f66e0ac16b23fd5394426607275670f0df7e8fe10f367060c70360e9c8
import argparse
import re
from pathlib import Path

import pytest

from clutch import __main__ as entry
from clutch import ask
from clutch.config import load_config
from tests.config_helpers import VALID

pytestmark = pytest.mark.disk_io_skip

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def prompts(tmp_path):
    (tmp_path / "config.yaml").write_text(VALID.replace("state_dir: .clutch", "state_dir: custom/state"))
    config = load_config(None, cwd=tmp_path)
    return {
        kind: ask.render(kind, "" if kind in ("plan-ticket-drain", "drain-loop") else "unique-stem", config, tmp_path) for kind in ("plan-ticket-drain", "author", "review", "drain-loop", "running")
    }


def test_plan_ticket_drain_prompt_content(prompts):
    text = prompts["plan-ticket-drain"]
    for phrase in (
        "docs/roadmap.md",
        "standing delegation",
        "conduct files",
        "explicit override",
        "the engine authored",
        "clutch host doctor",
        "clutch provider probe",
        "clutch release bump --minor",
        "never twice",
        "clutch prompt drain-loop",
        "clutch prompt diagnose",
        "clutch prompt drafts",
        "clutch prompt box",
        "clutch prompt running",
        "clutch ticket confirm --yes",
        "clutch ticket reject --yes",
        "clutch box suggest",
        "No person is in the loop",
        "Proposed",
        "different model family",
        "counted in runs",
        "Never push",
        "while a ticket runs",
        "in parallel",
        "before the first drain",
        "the tick it appears",
        "roadmap_row",
        "clutch roadmap author --ahead",
        "drift failure",
        "at most 3",
        "confirmed, unmerged ticket",
        "clutch prompt author",
        "clutch prompt review",
        "never hold",
        "clutch roadmap status",
        "clutch engine stop",
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
    assert text.index("conduct files") < text.index("clutch host doctor") < text.index("clutch provider probe") < text.index("clutch prompt drain-loop")
    assert text.index("standing delegation") < text.index("clutch ticket confirm --yes")
    assert "at most 4" not in text
    assert "about 25 minutes" not in text
    assert "top up with" not in text
    assert "Let the driver author" not in text
    assert "Hand-author only when the driver cannot" not in text
    assert not text.startswith("/loop")


def test_author_prompt_content(prompts):
    text = prompts["author"]
    for phrase in (
        "`unique-stem`",
        "tickets/unique-stem/ticket.md",
        "clutch ticket new unique-stem --kind",
        "--evidence",
        "clutch host docs",
        "clutch ticket lint unique-stem",
        "clutch ticket review unique-stem",
        "clutch view status",
        "clutch box suggest",
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
    assert text.index("clutch ticket new unique-stem") < text.index("clutch ticket lint unique-stem") < text.index("clutch ticket review unique-stem")


def test_review_prompt_is_audit(prompts):
    text = prompts["review"]
    for phrase in (
        "`unique-stem`",
        "tickets/unique-stem/ticket.md",
        "clutch host docs",
        "clutch view status",
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
        for phrase in ("${", "./dev.py", "uv run", "/home/", ".claude", "bash", "fungo", "codex", "qwen", "ollama", "gemini"):
            assert phrase not in text.lower(), phrase


def test_prompts_name_only_existing_verbs(prompts):
    parser = entry._parser()
    commands = next(a.choices for a in parser._actions if isinstance(a, argparse._SubParsersAction))
    groups = {name: action.choices for name, parser in commands.items() for action in parser._actions if isinstance(action, argparse._SubParsersAction)}
    for text in prompts.values():
        matches = re.findall(r"`clutch ([a-z-]+)(?: ([a-z-]+))?", text)
        assert matches
        for first, second in matches:
            assert first in commands
            if first in groups and second:
                assert second in groups[first]


def test_docs_list_new_prompt_kinds():
    running = (ROOT / "clutch/docs/host-running.md").read_text()
    row = next(line for line in running.splitlines() if line.startswith("| `prompt` |"))
    assert "plan-ticket-drain" in row and "author" in row
    lines = (ROOT / "docs/how-clutch-works.md").read_text().splitlines()
    assert any(line.startswith("| `prompt author <stem>` |") for line in lines)
    assert any(line.startswith("| `prompt plan-ticket-drain` |") for line in lines)
    assert any(line.startswith("| `prompt <diagnose") and "audits" in line for line in lines)
