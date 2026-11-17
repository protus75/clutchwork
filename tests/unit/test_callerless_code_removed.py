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
