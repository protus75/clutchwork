# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Unit test that view events prints one upgrade line for a serve_upgrade_pending signal, does not repeat it, and filters upgrade rows from the engine log
# relates: [clutch/events.py]
# owner: clutch/events.py
# verified: a6482110
# hash: 19fb4e1a52a9d0ca7e904126ccbe141872d6aea009406ca340a69f7ecb413d31
from clutch import events


def test_upgrade_delta_and_log_filter(monkeypatch):
    monkeypatch.setattr(events.observe, "recent_steps", lambda state, log, count: log)
    seen, lines = events.changes(None, [], [], None)
    assert lines == []
    signal = {"type": "signal", "ticket": None, "body": {"signal": "serve_upgrade_pending"}}
    seen, lines = events.changes(seen, [signal], [{"kind": "upgrade", "ts": "1", "text": "noise"}], None)
    assert lines == ["upgrade - engine code changed; no new tickets start until running work finishes and serve restarts -- clutch view watch"]
    assert events.changes(seen, [signal], [], None)[1] == []
