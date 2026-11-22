"""The help registry builds entirely from injected document text."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Unit tests that the help registry builds from injected document text, covers every snapshot vocabulary value and raises on unresolved links
# relates: [clutch/box.py, clutch/help.py, clutch/observe.py, clutch/stats.py, clutch/status.py]
# owner: engine
# verified: 9d19a72e
# hash: 1f9af826fb480ec3ef7ac7ea146d0567dc0b284487d0f49270e60dc601ce0045

from datetime import datetime, timezone
from typing import get_args

import pytest

from clutch.box import MessageClass
from clutch.help import COMMANDS, TOPICS, help_map, help_pick, topic_text
from clutch.observe import STEP_KINDS
from clutch.stats import project_stats
from clutch.status import SETTLED


def documents():
    return {
        "host-contract.md": "# Host contract\n\n## VS Code extension\n",
        "host-running.md": "\n".join(f"| `{entry['verb']}` | Yes | Description of {entry['verb']}. |" for entry in TOPICS.values() if "verb" in entry),
    }


def build(docs):
    return help_map(lambda path: docs[path.name], "https://example.test/repo")


def test_topic_shape():
    result = build(documents())
    assert set(result) == set(TOPICS)  # Omitting a topic must fail.
    for key, entry in result.items():
        assert entry["text"] == entry["what"] and len(entry["text"].splitlines()) == 1
        assert "Before:" not in entry["text"] and "After:" not in entry["text"]
        assert "before" not in entry and "after" not in entry
        assert "before" not in TOPICS[key] and "after" not in TOPICS[key]
        if not key.startswith("verb."):
            assert topic_text(key) == entry["what"]


def test_vocabularies_covered():
    expected = {
        "section": {"blocked", "queued", "running", "merged"},
        "status": {"invalid", "new", "draft", "held_change", "held_operator", "waits_on", "not_eligible", "interrupted", "retry_pending", "after", "ready", "running", "merged", "already_satisfied"}
        | SETTLED,
        "step": set(STEP_KINDS.values()),
        "box": set(get_args(MessageClass)),
        "boxOutcome": {"pending", "reopened", "author", "tombstone", "declined"},
        "stat": set(project_stats([], {}, {}, now=datetime(2026, 1, 1, tzinfo=timezone.utc), window="7d")),
        "verb": {"drain", "serve", "stop", "kill", "status", "retro"},
        "lock": {"engine", "commit"},
        "verdict": {"decisions"},
    }
    for kind, names in expected.items():
        assert {f"{kind}.{name}" for name in names} <= TOPICS.keys()  # New vocabulary values require help.
    assert "priority" in TOPICS
    assert set(COMMANDS.values()) <= TOPICS.keys()


def test_verdict_decisions_link():
    assert build(documents())["verdict.decisions"]["link"]["url"].endswith("/blob/main/docs/how-clutch-works.md#73-control")


def test_verb_what_follows_run_guide():
    docs = documents()
    docs["host-running.md"] = docs["host-running.md"].replace("Description of ticket review.", "A `revised` review description.")
    assert build(docs)["verb.review"]["what"] == "A revised review description."  # A copied description would be stale.


def test_unresolved_link_raises():
    docs = documents()
    docs["host-contract.md"] = docs["host-contract.md"].replace("VS Code extension", "Renamed")
    with pytest.raises(LookupError, match=r"view.clutch.details.*VS Code extension.*host-contract.md"):
        build(docs)
    docs = documents()
    docs["host-running.md"] = docs["host-running.md"].replace("| `ticket review` |", "| `renamed` |")
    with pytest.raises(LookupError, match=r"verb.review.*review.*host-running.md"):
        build(docs)


def test_help_pick_list():
    result = build(documents())
    items = help_pick(result)
    kinds = list(dict.fromkeys(key.partition(".")[0] for key in result))
    assert [item["label"] for item in items if item.get("kind") == "separator"] == kinds
    current = None
    for item in items[:-1]:
        if item.get("kind") == "separator":
            current = item["label"]
        else:
            key = item["topic"]
            assert key in result and key.partition(".")[0] == current
            assert item["detail"] == result[key]["what"] and item["description"] == result[key]["link"]["label"]
    assert items[-1]["command"] == "clutch.openSettings" and "topic" not in items[-1]
