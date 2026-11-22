# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Checks that observe.current_step ignores events older than the run's start time, uses events at or after it to set the step and time, and counts an event exactly at the start time.
# relates: [clutch/observe.py]
# owner: clutch/observe.py
# verified: 778fd8bc
# hash: b941d2d7b0e54950f9bb92cd9ddf55e46c313c7a42988ee646231631c785b609
from clutch.observe import current_step

T0 = "2026-11-22T13:31:16+00:00"
FLOOR = "2026-11-22T15:17:16+00:00"
T1 = "2026-11-22T15:18:09+00:00"
STALE = {"event": "stage_end", "stem": "alpha", "surface": "requisition_review", "ts": T0}


def test_stale_event_does_not_set_step_or_time():
    assert current_step([STALE], "alpha", FLOOR) == ("Starting", "", None)


def test_current_run_event_sets_step_and_time():
    current = {"event": "stage_start", "stem": "alpha", "surface": "requisition_review", "ts": T1}
    assert current_step([STALE, current], "alpha", FLOOR) == ("Requisition", T1, "requisition_review")


def test_event_at_floor_is_included():
    current = {"event": "stage_start", "stem": "alpha", "surface": "requisition_review", "ts": FLOOR}
    assert current_step([STALE, current], "alpha", FLOOR) == ("Requisition", FLOOR, "requisition_review")
