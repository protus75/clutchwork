"""Shared view topics resolve through the ordinary help registry."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Checks that the shared view help topics (dashboard, help, lifecycle) resolve through the help registry as one-line entries in the view section of the help picker.
# relates: [clutch/help.py]
# owner: clutch/help.py
# verified: 4fded5bb
# hash: f511adc47654c2df9bbfd82ada07f94b512e9e7e9723eeb9bf86ce249eb8e229

from clutch.help import TOPICS, help_map, help_pick


def test_shared_view_topics():
    docs = {
        "host-contract.md": "## VS Code extension\n",
        "host-running.md": "\n".join(f"| `{entry['verb']}` | Yes | Description of {entry['verb']}. |" for entry in TOPICS.values() if "verb" in entry),
    }
    result = help_map(lambda path: docs[path.name], "https://example.test")
    items = help_pick(result)
    start = next(i for i, item in enumerate(items) if item.get("kind") == "separator" and item["label"] == "view")
    end = next(i for i in range(start + 1, len(items)) if items[i].get("kind") == "separator")
    for name in ("dashboard", "help", "lifecycle"):
        key = f"view.clutch.{name}"
        assert key in TOPICS
        assert result[key]["text"] == result[key]["what"] and len(result[key]["text"].splitlines()) == 1 and result[key]["text"]
        assert key in [item.get("topic") for item in items[start + 1 : end]]
