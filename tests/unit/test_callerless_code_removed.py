# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test callerless code removed
# relates: [clutch/effects.py, clutch/git.py, clutch/heartbeat.py, clutch/requisition.py, clutch/timers.py, clutch/watchdog.py]
# owner: engine
# verified: 595b9e84
# hash: 8298a81877b7ffd40a1d59ce35fc7c57ee0ec11cefc78bc361a6a194395cce64
from clutch import driver, effects, git, heartbeat, requisition, timers, watchdog


def test_removed_and_retained_symbols():
    for owner, name in [
        (heartbeat, "is_fresh"),
        (timers.Timers, "wait_next"),
        (git.Git, "branch"),
        (effects, "effect"),
        (requisition, "dependent_errors"),
        (requisition, "test_sources"),
        (driver.Driver, "panel_members"),
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
