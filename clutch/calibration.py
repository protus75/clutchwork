"""Compare ticket estimates with journaled Implement call durations."""

import re
from datetime import datetime

from clutch.journal import EventType
from clutch.stats import _summary
from clutch.tickets import ticket_path

ESTIMATE_CALIBRATION = "estimate_calibration"
_IMPLEMENT = re.compile(r"llm/([^/]+)/[^/]+/implement/[^/]+/[^/]+")
_EXPECTED = re.compile(r"^- expected: (\d+)m$", re.MULTILINE)


def implement_runs(events):
    intents = {}
    runs = []
    for event in events:
        match = _IMPLEMENT.fullmatch(event.key or "")
        if not match:
            continue
        if event.type == EventType.EFFECT_INTENT:
            intents[event.key] = datetime.fromisoformat(event.ts)
        elif event.type == EventType.EFFECT_COMPLETION and event.key in intents and isinstance(event.body.get("cost"), dict):
            cost = event.body["cost"]
            minutes = (datetime.fromisoformat(event.ts) - intents[event.key]).total_seconds() / 60
            runs.append((match.group(1), cost["provider"], cost["model"], minutes))
    return runs


def calibrate(journal, fs, repo, every):
    groups = {}
    for stem, provider, model, minutes in implement_runs(journal.read())[-every:]:
        try:
            ticket = fs.read_bytes(repo / ticket_path(stem)).decode("utf-8")
        except OSError, UnicodeError:
            continue
        match = _EXPECTED.search(ticket)
        if match:
            expected, actual = groups.setdefault((provider, model), ([], []))
            expected.append(int(match.group(1)))
            actual.append(minutes)
    rows = []
    for (provider, model), (expected, actual) in sorted(groups.items()):
        estimates, durations = _summary(expected), _summary(actual)
        rows.append({"provider": provider, "model": model, "runs": len(actual), "expected_p50": estimates["p50"], "actual_p50": durations["p50"], "actual_p90": durations["p90"]})
    journal.append(EventType.SIGNAL, {"signal": ESTIMATE_CALIBRATION, "window": every, "rows": rows})
    return rows


def render(rows):
    return "".join(f"{r['provider']}/{r['model']}: {r['runs']} runs, estimate p50 {r['expected_p50']}m, actual p50 {r['actual_p50']}m, actual p90 {r['actual_p90']}m\n" for r in rows) or "none\n"
