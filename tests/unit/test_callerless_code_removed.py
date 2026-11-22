# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Asserts removed callerless symbols stay absent from timers, git, effects, requisition, driver and watchdog while their retained neighbours still exist
# relates: [clutch/effects.py, clutch/git.py, clutch/requisition.py, clutch/timers.py, clutch/watchdog.py]
# owner: engine
# verified: 5214eb3e
# hash: 8595d9eaca280d1111cdf69de599848a27afb29161a34d22984bb959baa01b3a
from clutch import driver, effects, git, requisition, timers, watchdog


def test_removed_and_retained_symbols():
    for owner, name in [
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
