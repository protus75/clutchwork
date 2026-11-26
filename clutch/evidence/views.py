"""Pure interpretation and rendering of stored evidence views."""

import json
from collections import Counter

from clutch.evidence import antigravity, claude, codex
from clutch.evidence.store import SKIP


def normalizer(provider):
    return {"claude": claude, "qwen": claude, "codex": codex, "antigravity": antigravity}.get(provider)


def build_view(start, stdout, times_ns, put_blob):
    module = normalizer(start.provider.name)
    return {
        "schema": "clutch.evidence.events/1.0",
        "normalizer": module.NORMALIZER_ID,
        "unverified": start.provider.name not in module.VERIFIED_PROVIDERS,
        "events": [event.model_dump(by_alias=True) for event in module.normalize(stdout, times_ns, put_blob)],
    }


def show_lines(start, end, views):
    lines = []
    for name, record in (("start", start), ("end", end)):
        value = "missing" if record is None else "skipped (unknown major version)" if record is SKIP else json.dumps(record.model_dump(by_alias=True), indent=2)
        lines.append(f"{name}.json: {value}")
    for view in views:
        lines.append(f"normalized/{view['normalizer']} unverified={view['unverified']}")
        for event in view["events"]:
            lines.append(f"{event['seq']} {event['t_ms']} {event['kind']} {event['native_type']}")
    return lines


def coverage(records, skipped=0):
    """Aggregate all stored view events by provider and CLI version."""
    groups = {}
    for start, views in records:
        if start is SKIP:
            skipped += 1
            continue
        key = (start.provider.name, start.provider.cli_version)
        group = groups.setdefault(key, {"total": 0, "unknown": Counter()})
        for view in views:
            for event in view["events"]:
                group["total"] += 1
                if event["kind"] == "unknown":
                    group["unknown"][event["native_type"]] += 1
    rows = []
    for (provider, version), group in sorted(groups.items(), key=lambda item: (item[0][0], item[0][1] or "")):
        total, unknown = group["total"], group["unknown"]
        rows.append(
            {
                "provider": provider,
                "cli_version": version,
                "known_pct": 100.0 * (total - unknown.total()) / total if total else 0.0,
                "unknown": sorted(unknown.items(), key=lambda item: (-item[1], item[0])),
            }
        )
    return rows, skipped
