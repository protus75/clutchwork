"""Actionable changes for a supervising operator."""

import base64
import binascii
import json
import math
import time

from clutch import observe, status
from clutch.enginelog import engine_log_path

POLL_SECONDS = 5
EVENTS = ("start", "settle", "reject_queue", "reject_release", "draft", "gate", "release", "upgrade", "engine_start", "engine_stop", "engine_lost")


def changes(seen, events, log, state):
    queue = status.reject_queue(observe.as_events(events))
    rows = sorted(observe.recent_steps(state, log, len(log)), key=lambda row: row["ts"])
    rows = [row for row in rows if row["kind"] in ("engine_start", "engine_stop", "engine_lost")]
    keys = {(row["kind"], row["ts"]) for row in rows}
    if seen is None or len(events) < seen[0]:
        gates = {}
        for event in events:
            body = event.get("body", {})
            if event.get("type") == "signal" and body.get("signal") == "roadmap_gate":
                gates[body["release"]] = body["passed"]
        return (len(events), set(queue), keys, gates), []

    gates = seen[3].copy()
    current = (len(events), set(queue), seen[2] | keys, gates)

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
            if signal == "serve_upgrade_pending":
                lines.append("upgrade - engine code changed; no new tickets start until running work finishes and serve restarts -- clutch view watch")
            elif signal == "ticket_intake" and body.get("state") == "draft" and body.get("source", "").startswith("box:"):
                lines.append(f"draft {stem} {body['source']} -- clutch prompt drafts")
            elif signal == "roadmap_gate":
                release, passed = body["release"], body["passed"]
                if release not in gates or gates[release] != passed:
                    result = "passed" if passed else "failed"
                    lines.append(f"gate - {release} {result} -- clutch roadmap status")
                gates[release] = passed
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


def encode_cursor(seen):
    offset, reject, engine, gates = seen
    data = {"v": 1, "offset": offset, "reject": sorted(reject), "engine": sorted(engine), "gates": gates}
    return base64.urlsafe_b64encode(json.dumps(data).encode("utf-8")).decode("ascii")


def decode_cursor(token: str):
    try:
        data = json.loads(base64.b64decode(token, altchars=b"-_", validate=True).decode("utf-8"))
        if not isinstance(data, dict) or set(data) != {"v", "offset", "reject", "engine", "gates"}:
            raise ValueError("invalid cursor envelope")
        offset, reject, engine, gates = (data[k] for k in ("offset", "reject", "engine", "gates"))
        if (
            type(data["v"]) is not int
            or data["v"] != 1
            or type(offset) is not int
            or offset < 0
            or not isinstance(reject, list)
            or any(not isinstance(x, str) for x in reject)
            or not isinstance(engine, list)
            or any(not isinstance(x, list) or len(x) != 2 or any(not isinstance(y, str) for y in x) for x in engine)
            or not isinstance(gates, dict)
            or any(not isinstance(k, str) or type(v) is not bool for k, v in gates.items())
        ):
            raise ValueError("invalid cursor fields")
        return offset, set(reject), {tuple(pair) for pair in engine}, gates
    except (ValueError, TypeError, UnicodeError, binascii.Error) as exc:
        raise ValueError("invalid event cursor") from exc


def wait_once(state, *, cursor=None, timeout=300.0, sleep=time.sleep, clock=time.monotonic, interval=POLL_SECONDS):
    if not math.isfinite(timeout) or timeout < 0 or not math.isfinite(interval) or interval <= 0:
        raise ValueError("timeout must be finite and nonnegative; interval must be finite and positive")
    seen = None if cursor is None else decode_cursor(cursor)
    deadline = clock() + timeout
    seen, lines = poll(state, seen)
    while not lines:
        remaining = deadline - clock()
        if remaining <= 0:
            return encode_cursor(seen), [], True
        sleep(min(interval, remaining))
        seen, lines = poll(state, seen)
    return encode_cursor(seen), lines, False
