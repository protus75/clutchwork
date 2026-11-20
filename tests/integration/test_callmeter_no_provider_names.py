from pathlib import Path

import clutch.watchdog


def test_watchdog_does_not_name_provider_events():
    source = Path(clutch.watchdog.__file__).read_text()
    assert all(name not in source for name in ("turn.completed", "item.started", "tool_use", "total_cost_usd", "cache_creation_input_tokens"))
