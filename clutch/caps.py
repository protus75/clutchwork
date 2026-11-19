"""Lineage-scoped failure-spine cap accounting."""

from collections.abc import Iterable, Mapping

from clutch.config import Caps, Config, ConfigSnapshot
from clutch.journal import Event, EventType, Journal
from clutch.llm import TIERS
from clutch.providers import ProviderSetupError, resolve
from clutch.tickets import Ticket

CONFLICT_RERUN_LIMIT = 2
CONFLICT_RERUN_ROAD = "split the ticket, or run it with parallel disabled"

CAPS = ("diagnosis", "retry", "infra", "premise_bounce")
# Audit recognizes historical hardening draws; supervise counts supervisor keeps and never routes.
DECLARED_CAPS = CAPS + ("hardening", "supervise")


def _check(cap: str) -> None:
    if cap not in DECLARED_CAPS:
        raise ValueError(f"cap {cap!r} is not one of DECLARED_CAPS {DECLARED_CAPS}")


def lineage(events: Iterable[Event], stem: str, *, actors: tuple[str, ...] = ("operator", "supervisor")) -> tuple[Event, ...]:
    """The one lineage window for both cap counts and effective capability."""
    history = tuple(events)
    keep = next(
        (
            i
            for i, e in reversed(list(enumerate(history)))
            if e.type == EventType.SIGNAL and e.ticket == stem and e.body.get("signal") == "reject_verdict" and e.body.get("verdict") == "keep" and e.body.get("actor") in actors
        ),
        -1,
    )
    return history[keep + 1 :]


def draws(events: Iterable[Event], stem: str, cap: str) -> int:
    """Count this stem's draws for one cap across all ticket content revisions."""
    _check(cap)
    return sum(e.type == EventType.CAP_CONSUMED and e.ticket == stem and e.body.get("cap") == cap for e in lineage(events, stem))


def conflict_reruns(events: Iterable[Event], stem: str) -> int:
    """Count conflict rerun signals in the current lineage."""
    return sum(e.type == EventType.SIGNAL and e.ticket == stem and e.body.get("signal") == "merge_conflict_rerun" for e in lineage(events, stem))


def conflict_rerun_spent(events: Iterable[Event], stem: str) -> bool:
    return conflict_reruns(events, stem) >= CONFLICT_RERUN_LIMIT


def supervise_draws(events: Iterable[Event], stem: str) -> int:
    """Count supervisor keeps within the operator lineage."""
    return sum(e.type == EventType.CAP_CONSUMED and e.ticket == stem and e.body.get("cap") == "supervise" for e in lineage(events, stem, actors=("operator",)))


def remaining(caps_config: Caps | ConfigSnapshot, events: Iterable[Event], stem: str, cap: str) -> int:
    _check(cap)
    return getattr(caps_config, cap) - draws(events, stem, cap)


def failed_attempt(terminal: Mapping) -> bool:
    return (
        terminal.get("to") in {"gate_failed", "premise_failed", "incomplete", "infra_error", "timeout"}
        and not (terminal.get("to") == "infra_error" and terminal.get("reason") == "provider_drought")
        and not (terminal.get("to") == "premise_failed" and terminal.get("stage") == "requisition")
    )


def failed_attempts(events: Iterable[Event], stem: str) -> int:
    """Failures are terminals, never cap draws; operator and supervisor keeps reset them."""
    return sum(e.type == EventType.STATE_TRANSITION and e.ticket == stem and failed_attempt(e.body) for e in lineage(events, stem))


def spent(caps_config: Caps | ConfigSnapshot, events: Iterable[Event], stem: str, *, pending: Mapping | None = None) -> str | None:
    # Materialize once: callers may pass a journal iterator, not only a list.
    history = tuple(events)
    if failed_attempts(history, stem) + (failed_attempt(pending) if pending is not None else 0) >= caps_config.attempts:
        return "attempts"
    return next((cap for cap in CAPS if remaining(caps_config, history, stem, cap) <= 0), None)


def consume(journal: Journal, stem: str, cap: str, ticket_sha: str, *, rung: dict[str, str] | None = None) -> None:
    _check(cap)
    if rung is not None and cap != "retry":
        raise ValueError("a rung belongs only on a retry cap draw")
    body = {"cap": cap, "ticket_sha": ticket_sha}
    if rung is not None:
        body["rung"] = rung
    journal.append(EventType.CAP_CONSUMED, body, ticket=stem)


def capability(ticket: Ticket, events: Iterable[Event]) -> tuple[str, str]:
    """The authored capability or the latest retry rung inside the lineage fold."""
    rung = next(
        (e.body["rung"] for e in reversed(lineage(events, ticket.stem)) if e.type == EventType.CAP_CONSUMED and e.ticket == ticket.stem and e.body.get("cap") == "retry" and "rung" in e.body), None
    )
    if rung is None:
        return ticket.frontmatter.agent_tier, ticket.frontmatter.agent_effort
    return rung["tier"], rung["effort"]


def next_rung(config: Config | ConfigSnapshot, tier: str, effort: str) -> dict[str, str] | None:
    """Move to the next distinct Implement model, then increase effort."""

    def model(level: str) -> tuple[str, str] | None:
        try:
            served = resolve(config, level, "implement")
        except ProviderSetupError:
            return None
        return served.provider.name, served.model

    current = model(tier)
    for higher in TIERS[TIERS.index(tier) + 1 :]:
        candidate = model(higher)
        if candidate is not None and candidate != current:
            return {"tier": higher, "effort": effort}
    if effort != "max":
        return {"tier": tier, "effort": TIERS[TIERS.index(effort) + 1]}
    return None


def spent_reason(cap: str) -> str:
    return f"{cap} cap spent"
