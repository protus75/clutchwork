# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test callmeter events
# relates: [clutch/providers.py, clutch/watchdog.py]
# owner: engine
# verified: 69d790e1
# hash: 13ceb3779e7c777a32122077b9d92dc61866aaca285c5d82c8a6d57e8bb5d2a1
from datetime import UTC, datetime
from unittest.mock import Mock

from clutch.providers import Served
from clutch.watchdog import Detector
from tests.unit.test_antigravity_adapter import provider


def meter_for(name):
    files = {}
    detector = Detector(
        expected_minutes=10, stuck_minutes=20, clock=lambda: datetime(2026, 1, 1, tzinfo=UTC), sleep=Mock(), observe=lambda: files.copy(), cap_wait=lambda: 0, log=Mock(), notify=Mock()
    )
    return detector, detector.start_call(Served(provider(name=name), "model")), files


def test_codex_tools_and_usage():
    detector, meter, _ = meter_for("codex")
    item = {"id": "tool-1", "type": "command_execution", "command": "pwd"}
    meter.consume({"type": "item.started", "item": item})
    assert meter.tools == {"tool-1"}
    meter.tools.clear()
    meter.consume({"type": "item.completed", "item": item})
    assert meter.tools == {"tool-1"}
    event = {"type": "turn.completed", "usage": {"input_tokens": 100, "output_tokens": 3, "reasoning_output_tokens": 50}}
    meter.consume(event)
    meter.consume(event)
    assert detector.tokens == 103
    event["usage"]["cache_write_input_tokens"] = 4
    meter.consume(event)
    assert detector.tokens == 107
    fresh, zero, _ = meter_for("codex")
    zero.consume({"type": "turn.completed", "usage": {"input_tokens": 0, "output_tokens": 0}})
    assert fresh.tokens == 0


def test_claude_usage_and_reasoning():
    detector, meter, _ = meter_for("claude")
    meter.consume({"type": "system", "subtype": "thinking_tokens", "estimated_tokens": 17})
    assert detector.tokens is None
    event = {"type": "assistant", "message": {"id": "m1", "content": [], "usage": {"input_tokens": 10, "output_tokens": 7}}}
    meter.consume(event)
    meter.consume(event)
    meter.consume({"type": "result", "total_cost_usd": 2})
    assert detector.tokens == 17
    assert detector.spend == 2 and meter.metered == 2


def test_rejected_event_observes_progress():
    detector, meter, files = meter_for("codex")
    meter.consume({"type": "turn.completed", "usage": {"input_tokens": 12, "output_tokens": 2}})
    meter.consume({"type": "item.started", "item": {"id": "prior", "type": "command_execution", "command": "pwd"}})
    files["changed"] = b"yes"
    meter.consume({"type": "item.started", "item": {"type": "command_execution", "command": "pwd"}})
    assert detector.progress_epoch == 1
    assert detector.tokens == 14 and meter.tools == {"prior"}
    assert meter.metered is None and detector.total_usd == 0.5 and detector.spend == 0
