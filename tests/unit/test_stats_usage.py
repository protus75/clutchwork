# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Tests the stats usage projection: per-provider and per-surface token counts, call failures, output tokens per merge, and no USD spend output.
# relates: [clutch/journal.py, clutch/stats.py]
# owner: clutch/stats.py
# verified: 4024355c
# hash: 52ebe63e769569b70b2b463e60e36312c6f7ec7d828db87e56f22f82a70db1c6
from datetime import UTC, datetime

from clutch.journal import Event, EventType
from clutch.stats import project_stats

NOW = datetime(2026, 1, 2, tzinfo=UTC)


def event(typ, body, key=None, ticket="one", ts="2026-01-01T12:00:00+00:00"):
    return Event(1, typ, ts, ticket, key, body)


def projection(merged=False):
    events = [
        event(EventType.EFFECT_COMPLETION, {"cost": {"provider": "claude", "input_tokens": 100, "output_tokens": 10, "usd": 5.0}}, "llm/one/1/implement/1/1"),
        event(EventType.EFFECT_COMPLETION, {"cost": {"provider": "codex", "input_tokens": 200, "output_tokens": 20, "usd": 0.5}}, "llm/two/1/review/1/1"),
        event(EventType.EFFECT_COMPLETION, {"cost": {"input_tokens": 7, "output_tokens": None}}, "llm/three/1/implement/1/1"),
        event(EventType.SIGNAL, {"signal": "provider_call_outcome", "provider": "claude", "failure_class": None}),
        event(EventType.SIGNAL, {"signal": "provider_call_outcome", "provider": "claude", "failure_class": "error"}),
        event(EventType.SIGNAL, {"signal": "provider_call_outcome", "provider": "codex", "failure_class": None}),
    ]
    if merged:
        events += [event(EventType.STATE_TRANSITION, {"to": "merged"}, ticket=stem) for stem in ("one", "two")]
    return project_stats(events, {}, {}, now=NOW, window="7d")


def test_usage_separates_providers_and_surfaces_without_usd():
    stats = projection()
    assert "spend" not in stats
    usage = stats["usage"]
    assert usage == {
        "by_provider": {
            "claude": {"calls": 2, "failures": 1, "input_tokens": 100, "output_tokens": 10, "output_tokens_per_merge": None},
            "codex": {"calls": 1, "failures": 0, "input_tokens": 200, "output_tokens": 20, "output_tokens_per_merge": None},
            "unknown": {"calls": 0, "failures": 0, "input_tokens": 7, "output_tokens": 0, "output_tokens_per_merge": None},
        },
        "by_surface": {
            "implement": {"claude": {"input_tokens": 100, "output_tokens": 10}, "unknown": {"input_tokens": 7, "output_tokens": 0}},
            "review": {"codex": {"input_tokens": 200, "output_tokens": 20}},
        },
    }


def test_usage_output_per_merge_uses_merge_count():
    providers = projection(merged=True)["usage"]["by_provider"]
    assert {name: row["output_tokens_per_merge"] for name, row in providers.items()} == {"claude": 5, "codex": 10, "unknown": 0}
