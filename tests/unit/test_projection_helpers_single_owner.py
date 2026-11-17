from datetime import UTC, datetime
from types import SimpleNamespace

from clutch import enginelog, journal, observe, status


def event(kind, ticket, body, ts="time", key=None):
    return journal.Event(1, kind, ts, ticket, key, body)


def test_latest_transitions_and_states():
    a1 = event("state_transition", "a", {"to": "running"})
    a2 = event("state_transition", "a", {"to": "gate_failed"})
    a3 = event("state_transition", "a", {"to": "running"})
    d = event("state_transition", "d", {"to": "merged"})
    events = [
        a1,
        event("state_transition", "b", {"to": "running"}),
        a2,
        event("signal", "c", {}),
        d,
        event("state_transition", None, {"to": "failed"}),
        a3,
        event("state_transition", "b", {"to": "rejected"}),
        event("state_transition", "d", {}),
    ]
    latest = status.latest_transitions(events)
    assert latest["a"] is a3
    assert latest["d"] is d
    assert "c" not in latest and None not in latest
    assert status.last_states(events) == {"a": "running", "b": "rejected", "d": "merged"}


def test_adapters_preserve_fields_and_latest_body():
    rows = [
        {"type": "state_transition", "ticket": "a", "ts": "t1", "body": {"to": "running"}, "key": "k"},
        {"type": "signal", "ticket": "b", "ts": "t0"},
        {"type": "state_transition", "ticket": "a", "ts": "t2", "body": {"to": "merged", "commit": "c1"}},
    ]
    adapted = observe.as_events(rows)
    assert vars(adapted[0]) == rows[0]
    assert vars(adapted[1]) == {**rows[1], "body": {}, "key": None}
    assert observe.last_bodies(adapted) == {"a": {"to": "merged", "commit": "c1", "ts": "t2"}}


def test_total_spend_filters_events_and_costs():
    events = [
        event("effect_completion", "a", {"cost": {"usd": 1.25}}),
        event("effect_completion", "a", {"cost": {"usd": 0.5}}),
        event("effect_intent", "a", {"cost": {"usd": 9}}),
        event("effect_completion", "a", {"cost": "invalid"}),
        event("effect_completion", "a", {}),
        event("effect_completion", "a", {"cost": {"tokens": 2}}),
    ]
    assert journal.total_spend(events) == 1.75
    assert journal.total_spend([]) == 0


def test_engine_log_uses_config_env_and_clock(tmp_path):
    config = SimpleNamespace(state_dir=tmp_path, providers=[SimpleNamespace(auth="KEY")], release=SimpleNamespace(pypi_token="TOKEN"))
    log = enginelog.engine_log(config, {"KEY": "s3cret-value"}, lambda: datetime(2026, 1, 2, tzinfo=UTC))
    assert log.path == tmp_path / "engine.log"
    log.event("probe", detail="s3cret-value")
    text = log.path.read_text()
    assert "[REDACTED:KEY]" in text
    assert "s3cret-value" not in text
