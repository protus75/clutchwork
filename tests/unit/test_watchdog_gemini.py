# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test watchdog gemini
# relates: [clutch/providers.py, clutch/watchdog.py, tests/unit/test_gemini_adapter.py]
# owner: engine
# verified: 9a610809
# hash: 6ebc511d82f665f8bd19f7dc0f8de022fbbf2a354b77387367c473737a31ccdb
from datetime import UTC, datetime
from unittest.mock import Mock

from clutch.providers import Served, _events
from clutch.watchdog import Detector
from tests.unit.test_gemini_adapter import T17, provider


def test_meter_reads_gemini_tools_and_stats():
    detector = Detector(expected_minutes=10, stuck_minutes=20, clock=lambda: datetime(2026, 1, 1, tzinfo=UTC), sleep=Mock(), observe=lambda: {}, cap_wait=lambda: 0, log=Mock(), notify=Mock())
    meter = detector.start_call(Served(provider(), "gemini-2.5-flash"))
    for event in _events(T17):
        meter.consume(event)
    assert meter.tools == {"update_topic__call_4935615467816418684", "write_file__call_4935615467816417309", "run_shell_command__call_4935615467816415934"}
    assert detector.tokens == 22168
    assert detector.spend == 0.5
    meter.complete()
    assert detector.bases == {}
