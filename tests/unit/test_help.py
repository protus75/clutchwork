"""The help registry builds entirely from injected document text."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: The help registry builds entirely from injected document text.
# relates: [clutch/box.py, clutch/help.py, clutch/observe.py, clutch/stats.py, clutch/status.py]
# owner: engine
# verified: 0a308920
# hash: f7465624251ba52b674c908e4bf3d48e64097ebc320e8284a50c86a58c57135a

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
        lines = entry["text"].splitlines()
        assert len(lines) == 3  # Missing or extra lines must fail.
        assert lines[0] == entry["what"] and lines[0].endswith(".") and len(lines[0]) > 1
        assert lines[1].startswith("Before: ") and lines[1][8:]
        assert lines[2].startswith("After: ") and lines[2][7:]
        if not key.startswith("verb."):
            assert topic_text(key) == entry["text"]  # Separate text renderers must agree.


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
