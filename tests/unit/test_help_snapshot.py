from datetime import datetime, timezone

from clutch.help import TOPICS, topic_text
from clutch.observe import STATUS_KEYS
from clutch.stats import project_stats, stats_tree
from clutch.status import SETTLED


def test_status_keys_covered():
    assert set(STATUS_KEYS) == {
        "invalid",
        "new",
        "draft",
        "held_change",
        "held_operator",
        "waits_on",
        "not_eligible",
        "interrupted",
        "retry_pending",
        "after",
        "ready",
        "running",
        "merged",
        "already_satisfied",
    }
    assert all(f"status.{key}" in TOPICS for key in STATUS_KEYS)
    assert SETTLED <= set(STATUS_KEYS)


def test_stats_tree_tooltips():
    stats = project_stats([], {}, {}, now=datetime(2026, 1, 1, tzinfo=timezone.utc), window="7d")
    rows = stats_tree(stats)
    assert len(rows) == len(stats)
    for key, row in zip(stats, rows):
        assert row["tooltip"] == topic_text(f"stat.{key}")
        assert all("tooltip" not in child for child in row["children"])
