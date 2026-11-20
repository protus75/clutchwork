# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test callerless code removed
# relates: [clutch/effects.py, clutch/git.py, clutch/heartbeat.py, clutch/requisition.py, clutch/timers.py, clutch/watchdog.py]
# owner: engine
# verified: 0a308920
# hash: eb5dddc292e35dfff8b333e0b60d7473e1eecbe09aea81dcf743e96789970a37
from clutch import effects, git, heartbeat, requisition, timers, watchdog


def test_removed_and_retained_symbols():
    for owner, name in [
        (heartbeat, "is_fresh"),
        (timers.Timers, "wait_next"),
        (git.Git, "branch"),
        (effects, "effect"),
        (requisition, "RequisitionGate"),
        (requisition, "base_render_chars"),
        (watchdog.Detector, "watch"),
    ]:
        assert not hasattr(owner, name)
    for owner, name in [
        (git.Git, "init"),
        (git.Git, "branch_delete"),
        (timers.Timers, "fire_due"),
        (effects.Effects, "run"),
        (requisition, "_base_render"),
        (watchdog, "watch_deadline"),
        (watchdog.Detector, "start_call"),
    ]:
        assert hasattr(owner, name)
