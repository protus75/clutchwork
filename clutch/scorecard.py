"""Pure journal-window surface accounting."""

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from pydantic import ValidationError

from clutch.artifacts import ReviewVerdict
from clutch.driver import unwrap_fence
from clutch.gates import ENGINE_GATE_CODES
from clutch.journal import EventType
from clutch.llmeffect import member_index
from clutch.panel import PanelMember, findings_union
from clutch.retro import Window, measurements


@dataclass(frozen=True)
class SurfaceScorecardRow:
    surface: str
    evaluated_tickets: int
    catches: int
    escapes: int
    bypass_count: int
    catch_rate: float
    escape_rate: float
    prune_candidate: bool


PANEL_OUTCOMES = ("no_panel_reviews", "no_cost_data", "measured")


@dataclass(frozen=True)
class PanelSlotRow:
    slot: int
    reviews: int
    unique_catches: int
    unique_per_100: float


@dataclass(frozen=True)
class PanelKindRow:
    kind: str
    reviews: int
    agreed_findings: int
    unique_catches: int


@dataclass(frozen=True)
class PanelScorecard:
    outcome: str
    panel_reviews: int
    slots: tuple[PanelSlotRow, ...]
    cost_multiplier: float | None
    kinds: tuple[PanelKindRow, ...] = ()


@dataclass(frozen=True)
class Scorecard:
    boundary: str
    merged_ticket_count: int
    spend_usd: float
    tokens: Mapping[str, Mapping[str, int]]
    signal_counts: Mapping[str, int]
    gate_failure_count: int
    surfaces: tuple[SurfaceScorecardRow, ...]
    panel: PanelScorecard


def project_scorecard(window: Window) -> Scorecard:
    """Fold collected observations and existing findings; never perform an effect."""
    evidence = window.evidence or measurements(window)
    evaluated, caught, bypasses, pending, used_bypasses = {}, {}, {}, {}, {}
    seen = set()
    escapes = {}
    groups, merges, signals_by_group = {}, {}, {}

    def observe(surface, ticket, failed=False, bypassed=False):
        evaluated.setdefault(surface, set()).add(ticket)
        caught.setdefault(surface, set())
        bypasses.setdefault(surface, 0)
        if failed and not bypassed:
            pending.setdefault(ticket, set()).add(surface)

    for index, event in enumerate(window.events):
        stem, body = event.ticket, event.body
        if event.type == EventType.EFFECT_COMPLETION:
            if event.key in seen:
                continue
            seen.add(event.key)
            if (event.key or "").startswith("escape-attribution/"):
                result = body["result"]
                for match in result["matches"]:
                    for surface in match["surfaces"]:
                        escapes.setdefault(surface, set()).add((result["box_id"], match["ticket"]))
            used = set()
            for ticket, code, verdict, bypassed in window.completed_checks.get(event.key, ()):
                observe(code, ticket, verdict == "fail", bypassed)
                used_bypasses[ticket, code] = bypassed
                if bypassed and (ticket, code) not in used:
                    bypasses[code] += 1
                    used.add((ticket, code))
            parts = (event.key or "").split("/")
            slot = member_index(event.key)
            if slot is not None and parts[3] == "review" and stem and isinstance(body, dict):
                cost = body.get("cost")
                usd = 0.0 if "cost" not in body else cost.get("usd") if isinstance(cost, dict) else None
                if isinstance(usd, (int, float)) and not isinstance(usd, bool):
                    group = groups.setdefault((stem, parts[2].split("-")[1], parts[4]), {"first": index, "last": index, "slots": {}})
                    group["last"] = index
                    member = group["slots"].setdefault(slot, {"cost": 0.0, "reply": None, "seq": -1})
                    member["cost"] += usd
                    try:
                        reply = ReviewVerdict.model_validate_json(unwrap_fence(body["result"]["text"]))
                    except KeyError, TypeError, AttributeError, ValidationError:
                        pass
                    else:
                        if int(parts[5]) > member["seq"]:
                            member["reply"], member["seq"] = reply, int(parts[5])
            if len(parts) == 6 and parts[0] == "llm" and parts[3] == "review" and stem:
                try:
                    verdict = ReviewVerdict.model_validate_json(unwrap_fence(body["result"]["text"]))
                except KeyError, TypeError, AttributeError, ValidationError:
                    continue  # Schema-invalid calls are spend, not a review verdict.
                observe("review", stem, verdict.verdict in {"snag", "rma"})
        elif event.type == EventType.SIGNAL and stem and isinstance(body, dict):
            attempt = body.get("attempt")
            if body.get("signal") == "panel_facts" and body.get("surface") == "review" and type(attempt) is int:
                signals_by_group.setdefault((stem, str(attempt)), []).append((index, body))
        elif event.type == EventType.STATE_TRANSITION and stem:
            state = body.get("to")
            if state == "merged":
                merges.setdefault(stem, []).append(index)
            if state == "gate_failed":
                # A gate terminal's reason is the runner's comma-separated finding codes.
                for code in body.get("reason", "").split(","):
                    if code in ENGINE_GATE_CODES and not used_bypasses.get((stem, code), False):
                        observe(code, stem, True)
            if state in {"merged", "gate_failed", "abandoned", "rejected"}:
                for surface in pending.get(stem, ()):
                    caught[surface].add(stem)

    counts, panel_reviews, total_cost, baseline = {}, 0, 0.0, 0.0
    kind_counts = {}
    for (stem, _run, attempt), group in sorted(groups.items(), key=lambda item: item[1]["last"]):
        slots = group["slots"]
        present = sorted(slot for slot, member in slots.items() if member["reply"] is not None)
        if len(present) < 2:
            continue
        panel_reviews += 1
        total_cost += sum(slots[slot]["cost"] for slot in present)
        baseline += slots[present[0]]["cost"]
        for slot in present:
            counts.setdefault(slot, [0, 0])[0] += 1
        replies = [slots[slot]["reply"] for slot in present]
        members = [PanelMember(provider="unknown", model="unknown", verdict=reply.verdict) for reply in replies]
        next_group = min(
            (
                other["first"]
                for (other_stem, other_run, other_attempt), other in groups.items()
                if other_stem == stem and other_attempt == attempt and other_run != _run and other["first"] > group["last"]
            ),
            default=len(window.events),
        )
        candidates = [body for index, body in signals_by_group.get((stem, attempt), ()) if group["last"] < index < next_group]
        kind = None
        if candidates:
            signal = candidates[-1]
            raw_members = signal.get("members")
            if isinstance(raw_members, list) and len(raw_members) == len(present) and signal.get("agreement_kind") in ("models", "samples"):
                try:
                    members = [PanelMember.model_validate(member) for member in raw_members]
                except ValidationError:
                    pass
                else:
                    kind = signal["agreement_kind"]
        _, facts = findings_union(replies, members)
        unique = 0
        if any(position > group["last"] for position in merges.get(stem, ())):
            for finding in facts.merged:
                if len(finding.members) == 1:
                    counts[present[finding.members[0]]][1] += 1
                    unique += 1
        if kind is not None:
            row = kind_counts.setdefault(kind, [0, 0, 0])
            row[0] += 1
            row[1] += sum(len(finding.members) >= 2 for finding in facts.merged)
            row[2] += unique
    panel_rows = tuple(PanelSlotRow(slot, reviews, catches, 100 * catches / reviews) for slot, (reviews, catches) in sorted(counts.items()))
    outcome = "no_panel_reviews" if not panel_reviews else "no_cost_data" if not baseline else "measured"
    kinds = tuple(PanelKindRow(kind, *kind_counts[kind]) for kind in ("models", "samples") if kind in kind_counts)
    panel = PanelScorecard(outcome, panel_reviews, panel_rows, total_cost / baseline if baseline else None, kinds)

    rows = []
    for surface in sorted(evaluated.keys() | escapes.keys()):
        count, catches = len(evaluated.get(surface, ())), len(caught.get(surface, ()))
        escaped = len(escapes.get(surface, ()))
        rows.append(
            SurfaceScorecardRow(surface, count, catches, escaped, bypasses.get(surface, 0), catches / count if count else 0, escaped / count if count else 0, count >= 25 and catches == escaped == 0)
        )
    tokens = MappingProxyType({direction: MappingProxyType(dict(evidence[f"{direction}_tokens"])) for direction in ("input", "output")})
    signals = MappingProxyType(dict(evidence["spikes"]))
    return Scorecard(window.boundary, evidence["merged_count"], evidence["usd"], tokens, signals, signals["gate-failure"], tuple(rows), panel)


def panel_lines(card: Scorecard) -> list[str]:
    panel = card.panel
    if panel.outcome == "no_panel_reviews":
        return []
    multiplier = f"{panel.cost_multiplier:.2f}" if panel.cost_multiplier is not None else "n/a"
    lines = [
        "",
        "## Panel scorecard",
        "",
        f"Panel reviews: {panel.panel_reviews}; cost multiplier: {multiplier}",
        "",
        "| Slot | Reviews | Unique catches | Unique catches per 100 reviews |",
        "| ---: | ---: | ---: | ---: |",
    ]
    lines.extend(f"| {row.slot} | {row.reviews} | {row.unique_catches} | {row.unique_per_100:.2f} |" for row in panel.slots)
    if panel.kinds:
        lines.extend(["", "| Agreement | Reviews | Agreed findings | Unique catches |", "| --- | ---: | ---: | ---: |"])
        lines.extend(f"| {row.kind} | {row.reviews} | {row.agreed_findings} | {row.unique_catches} |" for row in panel.kinds)
    return lines
