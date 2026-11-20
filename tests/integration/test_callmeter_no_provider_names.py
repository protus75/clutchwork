# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test callmeter no provider names
# relates: [clutch/watchdog.py]
# owner: clutch/watchdog.py
# verified: 148a8874
# hash: 73e92e02d34dfd622d9083fd2410124e9c227a7283c84dba48dcbf21a6d8ba14
from pathlib import Path

import clutch.watchdog


def test_watchdog_does_not_name_provider_events():
    source = Path(clutch.watchdog.__file__).read_text()
    assert all(name not in source for name in ("turn.completed", "item.started", "tool_use", "total_cost_usd", "cache_creation_input_tokens"))
