"""One supervisor attempt per operator lineage at an idle boundary."""

from collections.abc import Awaitable, Callable

from clutch.artifacts import Finding
from clutch.caps import lineage, spent, spent_reason, supervise_draws
from clutch.journal import EventType
from clutch.runner import Checkout, record_supervisor_keep, supervise_step
from clutch.stages import StageContext
from clutch.status import reject_queue
from clutch.tickets import parse_ticket, ticket_path


async def supervise_idle(checkout: Checkout, make_ctx: Callable[[], Awaitable[StageContext | None]]) -> None:
    events = checkout.journal.read()
    eligible = []
    for stem, terminal in reject_queue(events).items():
        cap = spent(checkout.config.caps, events, stem)
        if (
            "ticket_changed" in terminal.get("reason", "").split(",")
            or not (terminal.get("to") == "premise_failed" or terminal.get("to") == "gate_failed" and cap is not None)
            or supervise_draws(events, stem) >= checkout.config.caps.supervise
            or any(e.type == EventType.SIGNAL and e.ticket == stem and e.body.get("signal") == "supervisor_attempt" for e in lineage(events, stem, actors=("operator",)))
        ):
            continue
        eligible.append((stem, terminal, cap))
    if not eligible:
        return
    ctx = await make_ctx()
    if ctx is None:
        return
    for stem, terminal, cap in eligible:
        ticket = parse_ticket(stem, ctx.fs.read_bytes(ctx.repo / ticket_path(stem)).decode(), ctx.repo)
        attempt = sum(e.type == EventType.SIGNAL and e.ticket == stem and e.body.get("signal") == "supervisor_attempt" for e in events)
        lessons = tuple(
            dict.fromkeys(lesson for e in lineage(events, stem) if e.type == EventType.SIGNAL and e.ticket == stem and e.body.get("signal") == "diagnosis" for lesson in e.body.get("lessons", []))
        )
        finding = Finding(code=terminal["reason"], message=terminal["reason"], paved_road="review the supervisor proposal and keep or reject the ticket")
        await ctx.git.worktree_add_detached(ctx.repo, ctx.worktree(stem), "main")
        try:
            sha = await supervise_step(ctx, ticket, [finding], attempt=attempt, trigger=spent_reason(cap) if cap is not None else "premise_failed", lessons=lessons, key_scope="sup")
            if sha is not None:
                record_supervisor_keep(ctx, stem, sha)
        finally:
            await ctx.git.worktree_remove(ctx.repo, ctx.worktree(stem))
            await ctx.git.worktree_prune(ctx.repo)
