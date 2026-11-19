"""Actionable changes for a supervising operator."""

from clutch import observe, status
from clutch.enginelog import engine_log_path

POLL_SECONDS = 5
EVENTS = ("start", "settle", "reject_queue", "reject_release", "draft", "gate", "release", "engine_start", "engine_stop", "engine_lost")


def changes(seen, events, log, state):
    queue = status.reject_queue(observe.as_events(events))
    rows = sorted(observe.recent_steps(state, log, len(log)), key=lambda row: row["ts"])
    rows = [row for row in rows if row["kind"] in EVENTS[7:]]
    keys = {(row["kind"], row["ts"]) for row in rows}
    current = (len(events), set(queue), keys if seen is None else seen[2] | keys)
    if seen is None or len(events) < seen[0]:
        return (len(events), set(queue), keys), []

    lines = []
    for event in events[seen[0] :]:
        body = event.get("body", {})
        stem = event.get("ticket") or "-"
        if event.get("type") == "state_transition":
            target = body.get("to")
            if target == "running":
                lines.append(f"start {stem} -- clutch roadmap status")
            elif target in status.CLOSED:
                lines.append(f"settle {stem} {target} -- clutch roadmap status")
        elif event.get("type") == "signal":
            signal = body.get("signal")
            if signal == "ticket_intake" and body.get("state") == "draft" and body.get("source", "").startswith("box:"):
                lines.append(f"draft {stem} {body['source']} -- clutch prompt drafts")
            elif signal == "roadmap_gate":
                result = "passed" if body["passed"] else "failed"
                lines.append(f"gate - {body['release']} {result} -- clutch roadmap status")
            elif signal == "release":
                lines.append(f"release - {body['tag']} -- clutch roadmap status")
    for stem in sorted(set(queue) - seen[1]):
        lines.append(f"reject_queue {stem} {queue[stem]['to']} -- clutch prompt diagnose {stem}")
    for stem in sorted(seen[1] - set(queue)):
        lines.append(f"reject_release {stem} -- clutch view status")
    emitted = set(seen[2])
    for row in rows:
        key = (row["kind"], row["ts"])
        if key not in emitted:
            verb = "view status" if row["kind"] == "engine_start" else "prompt drain-loop"
            lines.append(f"{row['kind']} - {row['text']} -- clutch {verb}")
            emitted.add(key)
    return current, lines


def poll(state, seen):
    path = engine_log_path(state)
    try:
        log = observe.read_lines(path, 4000)
    except FileNotFoundError:
        log = []
    return changes(seen, observe.journal(state), log, state)


def stream(state, *, sleep, write, interval=POLL_SECONDS):
    seen = None
    while True:
        seen, lines = poll(state, seen)
        for line in lines:
            write(line)
        sleep(interval)
