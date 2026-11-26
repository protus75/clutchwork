# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Unit test that the watchdog call meter counts Antigravity tool steps and result token usage.
# relates: [clutch/providers.py, clutch/watchdog.py, tests/unit/test_antigravity_adapter.py]
# owner: clutch/watchdog.py
# verified: 69d790e1
# hash: 3b306d0bec5fb2293b7c80b9dd4017a7a69fa110bde494de1540792d8d0edf3b
from datetime import UTC, datetime
from unittest.mock import Mock

from clutch.providers import Served
from clutch.watchdog import Detector
from tests.unit.test_antigravity_adapter import provider


def test_meter():
    detector = Detector(expected_minutes=10, stuck_minutes=20, clock=lambda: datetime(2026, 1, 1, tzinfo=UTC), sleep=Mock(), observe=lambda: {}, cap_wait=lambda: 0, log=Mock(), notify=Mock())
    meter = detector.start_call(Served(provider(), "model"))
    meter.consume({"event": "step_update", "step_update": {"step_type": "tool", "state": "ACTIVE", "step_index": 2, "tool_name": "read_file"}})
    meter.consume({"event": "result", "result": {"status": "SUCCESS", "usage": {"input_tokens": 60, "cache_read_tokens": 40, "output_tokens": 7}}})
    assert meter.tools == {"2"} and detector.tokens == 107
