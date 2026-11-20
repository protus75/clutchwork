# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test baseline visual
# relates: [clutch/baseline.py, clutch/journal.py]
# owner: engine
# verified: 0a308920
# hash: dcbf11632382db7181b0250729a5b666fd582a7e965ab226305347dccc68b6e5
from types import SimpleNamespace

import pytest

from clutch import baseline
from clutch.journal import EventType


@pytest.fixture
def identity(monkeypatch):
    current = {"review_visual": {"spec_major": 2, "rows": {"medium": {"provider": "judge", "model": "model-a"}}}}
    monkeypatch.setattr(baseline, "visual_identity", lambda config, specs_dir: current)
    return current


def signal(verdict, identity):
    return SimpleNamespace(type=EventType.SIGNAL, body={"signal": "visual_baseline", "verdict": verdict, "identity": identity})


def test_latest_go_binds(identity):
    result = baseline.resolve_visual_baseline(None, [signal("NO_GO", identity), signal("GO", identity)], specs_dir=None)
    assert result.state == "GO" and result.binds


def test_absent(identity):
    result = baseline.resolve_visual_baseline(None, [], specs_dir=None)
    assert result.state == "ABSENT" and not result.binds


def test_latest_no_go(identity):
    result = baseline.resolve_visual_baseline(None, [signal("GO", identity), signal("NO_GO", identity)], specs_dir=None)
    assert result.state == "NO_GO" and not result.binds


@pytest.mark.parametrize(
    "changed",
    [
        {"review_visual": {"spec_major": 3, "rows": {"medium": {"provider": "judge", "model": "model-a"}}}},
        {"review_visual": {"spec_major": 2, "rows": {"medium": {"provider": "judge", "model": "model-b"}}}},
    ],
)
def test_stale_identity(identity, changed):
    result = baseline.resolve_visual_baseline(None, [signal("GO", changed)], specs_dir=None)
    assert result.state == "REVOKED" and not result.binds


@pytest.mark.parametrize("event", [SimpleNamespace(type=EventType.SIGNAL, body=[]), SimpleNamespace(type="unknown", body={})])
def test_malformed_event(identity, event):
    result = baseline.resolve_visual_baseline(None, [signal("GO", identity), event], specs_dir=None)
    assert result.state == "REVOKED" and not result.binds


def test_identity_exception_revokes(monkeypatch, identity):
    def fail(*args):
        raise ValueError("unavailable")

    monkeypatch.setattr(baseline, "visual_identity", fail)
    result = baseline.resolve_visual_baseline(None, [signal("GO", identity)], specs_dir=None)
    assert result.state == "REVOKED" and not result.binds
