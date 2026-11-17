"""Reviewed Rework orders and journal supersession."""

import asyncio
import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from clutch.artifacts import Artifact, Cost, Finding, NonBlank, StageResult
from clutch.driver import LlmStage
from clutch.gates import GateReport
from clutch.git import GitError
from clutch.journal import Event, EventType
from clutch.llm import AgentEffort, AgentTier
from clutch.mergequeue import ConflictHandoff
from clutch.requisition import review_ticket
from clutch.specs import RenderOverBound, load_spec, render
from clutch.stages import StageContext, _major
from clutch.status import last_states
from clutch.tickets import Ticket, TicketInvalid, _criteria, _sections, split_frontmatter, stem_findings, ticket_path, validate_ticket

REWORK_ORDER = "rework_order"
SUPERSEDES = "supersedes"


class TicketProposal(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", frozen=True)

    stem: NonBlank
    ticket: NonBlank


class ReworkReply(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", frozen=True)

    action: Literal["update", "split", "escalate"]
    tickets: list[TicketProposal]

    @model_validator(mode="after")
    def _shape(self) -> "ReworkReply":
        stems = [t.stem for t in self.tickets]
        if len(stems) != len(set(stems)):
            raise ValueError("proposal stems must be distinct")
        if (self.action == "update" and len(stems) != 1) or (self.action == "split" and len(stems) < 2) or (self.action == "escalate" and stems):
            raise ValueError("update needs one ticket, split at least two, escalate none")
        return self


class ReworkOrder(Artifact, ReworkReply):
    stem: NonBlank
    attempt: Annotated[int, Field(ge=0)]

    @model_validator(mode="after")
    def _identity(self) -> "ReworkOrder":
        if self.action == "update" and self.tickets[0].stem != self.stem:
            raise ValueError("update must retain the original stem")
        if self.action == "split" and self.stem in {t.stem for t in self.tickets}:
            raise ValueError("split must use fresh successor stems")
        return self


def _finding(message: str, road: str, *, path: str | None = None) -> Finding:
    return Finding(code="ticket_schema", path=path, message=message, paved_road=road)


@dataclass(frozen=True)
class Supervise:
    trigger: str
    lessons: tuple[str, ...]


def supervise_findings(stem: str, original: str, reply: ReworkReply) -> list[Finding]:
    path = ticket_path(stem)
    road = f"escalate to the operator: the stem stays in the Reject queue; edit {path}, then `clutch confirm {stem}`, or retire it with `clutch reject {stem}`"
    messages = []
    if reply.action == "split":
        messages.append("a supervisor edit cannot split the ticket")
    elif reply.action == "update":
        proposal = reply.tickets[0].ticket

        def sections(text: str) -> dict[str, str]:
            parts = split_frontmatter(text)
            return _sections(parts[1], path)[0] if parts else {}

        old, new = sections(original), sections(proposal)
        if proposal == original:
            messages.append("the proposal does not change the ticket text")
        if old.get("Goal / Why", "").strip() != new.get("Goal / Why", "").strip():
            messages.append("the proposal changes `## Goal / Why`")
        old_count = len(_criteria(old.get("Acceptance criteria", "")))
        new_count = len(_criteria(new.get("Acceptance criteria", "")))
        if new_count < old_count:
            messages.append(f"the proposal drops acceptance criteria ({new_count} of {old_count} remain)")
    return [Finding(code="supervise_edit", path=path, message=message, paved_road=road) for message in messages]


def review_prior(action, original_stem, original_ticket, snag_list, retry_findings, proposals, current_stem) -> str:
    return json.dumps(
        {
            "action": action,
            "original_stem": original_stem,
            "original_ticket": original_ticket,
            "snag_list": snag_list,
            "retry_findings": retry_findings,
            "sibling_proposals": [{"stem": p.stem, "ticket": p.ticket} for p in proposals if p.stem != current_stem],
            "sibling_note": "These tickets are part of the same rework order, are absent from the checkout you browse, and count as existing for dependency and fence checks.",
        }
    )


async def rework(
    ctx: StageContext,
    ticket: Ticket,
    text: str,
    findings: list[Finding],
    *,
    attempt: int,
    workspace: Path,
    tier: AgentTier,
    effort: AgentEffort,
    stuck_budget: float,
    handoff: ConflictHandoff | None = None,
    supervise: Supervise | None = None,
) -> StageResult:
    """Call only after admission unwinds; return proposals, never publish or retire tickets."""
    if handoff is not None and handoff.stem != ticket.stem:
        return StageResult(outcome="gate_failed", artifact=None, cost=Cost(), findings=[_finding("conflict handoff names a different ticket", "supply this ticket's queue-owned handoff")])
    spec = load_spec((ctx.specs_dir / "rework.md").read_text())
    head = await ctx.git.rev_parse(workspace, "HEAD")
    repository_head = await ctx.git.rev_parse(ctx.repo, "HEAD")
    # Review effects name successor identities too; those of THIS invocation are not prior use.
    history = ctx.driver.journal.read()
    identities = {e.ticket for e in history if e.ticket is not None}
    prefix = f"llm/{ticket.stem}/{attempt}/requisition_review/{attempt}/"
    review_seq = max((int(e.key.rsplit("/", 1)[-1]) for e in history if e.key is not None and e.key.startswith(prefix)), default=0)

    retry_findings: list[Finding] = []
    last_reply: ReworkReply | None = None

    def render_attempt(_: object, retry: list[Finding]) -> str:
        nonlocal retry_findings
        retry_findings = retry
        return render(
            spec,
            {
                "ticket": f"Original stem: {ticket.stem}\n\n{text}",
                "findings": json.dumps([f.model_dump() for f in findings], sort_keys=True),
                "conflict": handoff.model_dump_json() if handoff else "none",
                "supervise": json.dumps({"trigger": supervise.trigger, "lessons": list(supervise.lessons)}, sort_keys=True) if supervise else "none",
                "retry_findings": json.dumps([f.model_dump() for f in retry], sort_keys=True),
            },
        )

    async def review(artifact: BaseModel, call_seq: int) -> GateReport:
        nonlocal review_seq, last_reply
        assert isinstance(artifact, ReworkReply)
        last_reply = artifact
        if supervise is not None and (refusals := supervise_findings(ticket.stem, text, artifact)):
            return GateReport(code="ticket_schema", verdict="fail", findings=refusals)
        errors = []
        for proposal in artifact.tickets:
            errors.extend(stem_findings(proposal.stem))
            if artifact.action == "update" and proposal.stem != ticket.stem:
                errors.append(_finding("update must retain the original stem", "propose one ticket for " + ticket.stem))
            if artifact.action == "split" and (proposal.stem == ticket.stem or (ctx.repo / "tickets" / proposal.stem).exists() or proposal.stem in identities):
                errors.append(_finding(f"successor {proposal.stem!r} is not fresh", "choose a stem absent from ticket directories and journal identities"))
        if errors or artifact.action == "escalate":
            return GateReport(code="ticket_schema", verdict="fail" if errors else "pass", findings=errors)

        tree = ctx.config.state_dir / "rework" / ticket.stem / str(attempt) / str(call_seq)
        try:
            await ctx.git.worktree_add_detached(ctx.repo, tree, repository_head)
            for proposal in artifact.tickets:
                ctx.fs.write(tree / ticket_path(proposal.stem), proposal.ticket.encode())
            for proposal in artifact.tickets:
                try:
                    candidate = validate_ticket(proposal.stem, proposal.ticket, tree)
                    expected = {"source": ticket.frontmatter.source, "state": "confirmed", "agent_tier": ticket.frontmatter.agent_tier, "agent_effort": ticket.frontmatter.agent_effort}
                    for key, value in expected.items():
                        if getattr(candidate.frontmatter, key) != value:
                            errors.append(_finding(f"proposal must preserve {key}: {value}", f"set {key} to {value} in every proposal", path=ticket_path(proposal.stem)))
                    if artifact.action == "split" and ticket.stem in candidate.depends:
                        errors.append(_finding("a successor depends on the superseded original", "depend on a buildable sibling or original predecessor instead", path=ticket_path(proposal.stem)))
                except TicketInvalid as exc:
                    errors.extend(exc.findings)
            if errors:
                return GateReport(code="ticket_schema", verdict="fail", findings=errors)

            for proposal in artifact.tickets:
                verdict = await review_ticket(
                    ctx.driver,
                    repo=tree,
                    stem=proposal.stem,
                    text=proposal.ticket,
                    specs_dir=ctx.specs_dir,
                    coverage_map=ctx.config.state_dir / "coverage-map.json" if ctx.config.review.coverage_map is not None else None,
                    tier=tier,
                    stem_slot=ticket.stem,
                    run_seq=attempt,
                    attempt=attempt,
                    call_seq=review_seq + 1,
                    prior=review_prior(
                        artifact.action,
                        ticket.stem,
                        text,
                        [f.model_dump() for f in findings],
                        [f.model_dump() for f in retry_findings],
                        artifact.tickets,
                        proposal.stem,
                    ),
                    expected_budget=ticket.expected_minutes * 60.0,
                )
                review_seq += max(verdict.calls, 1)
                if verdict.verdict == "rma":
                    return GateReport(code="requisition_review", verdict="fail", findings=[f.model_copy(update={"code": "requisition_rma"}) for f in verdict.findings])
                if verdict.verdict == "approve":
                    ctx.driver.journal.append(
                        EventType.SIGNAL,
                        {
                            "signal": "requisition_verdict",
                            "verdict": "approve",
                            "ticket_sha": verdict.ticket_sha,
                            "provider": verdict.provider,
                            "model": verdict.model,
                            "spec_version": verdict.spec_version,
                        },
                        ticket=proposal.stem,
                    )
                errors.extend(verdict.findings)
            return GateReport(code="requisition_review", verdict="fail" if errors else "pass", findings=errors)
        finally:
            # The Driver can cancel a timed-out review while its disposable checkout needs removal.
            if tree.exists():
                cleanup = asyncio.create_task(ctx.git.worktree_remove(ctx.repo, tree))
                try:
                    await asyncio.shield(cleanup)
                except asyncio.CancelledError:
                    await cleanup
                    raise

    try:
        result = await ctx.driver.run(
            LlmStage(surface="rework", emits=ReworkReply, gates=[], render=render_attempt, review=review, terminal_findings=frozenset({"requisition_rma", "supervise_edit"})),
            ticket,
            ticket=ticket.stem,
            attempt=attempt,
            workspace=workspace,
            tier=tier,
            effort=effort,
            stuck_budget=stuck_budget,
            expected_budget=ticket.expected_minutes * 60.0,
            scope_fence=(),
        )
    except RenderOverBound as exc:
        return StageResult(outcome="premise_failed", artifact=None, findings=[exc.finding], cost=Cost())
    if result.outcome != "ok":
        return replace(result, artifact=last_reply) if supervise is not None and result.outcome == "gate_failed" else result
    reply = result.artifact
    assert isinstance(reply, ReworkReply)
    order = ReworkOrder(**reply.model_dump(), stem=ticket.stem, attempt=attempt, produced_by_spec_version=_major(spec), produced_at_sha=head)
    ctx.driver.journal.append(EventType.SIGNAL, {"signal": REWORK_ORDER, "attempt": attempt, "action": order.action}, ticket=ticket.stem, key=None)
    return replace(result, artifact=order)


def supersedes_maps(events: Iterable[Event]) -> dict[str, tuple[str, ...]]:
    return {e.ticket: tuple(e.body["successors"]) for e in events if e.type == EventType.SIGNAL and e.ticket is not None and e.body.get("signal") == SUPERSEDES}


def successor_leaves(stem: str, maps: Mapping[str, tuple[str, ...]]) -> frozenset[str]:
    if stem not in maps:
        return frozenset({stem})
    return frozenset(leaf for successor in maps[stem] for leaf in successor_leaves(successor, maps))


def settled_dependencies(events: Iterable[Event]) -> frozenset[str]:
    from clutch.drain import SETTLED

    history = tuple(events)
    maps, states = supersedes_maps(history), last_states(history)
    return frozenset(stem for stem in states.keys() | maps.keys() if all(states.get(leaf) in SETTLED for leaf in successor_leaves(stem, maps)))


def dead_dependencies(events: Iterable[Event]) -> frozenset[str]:
    history = tuple(events)
    maps, states = supersedes_maps(history), last_states(history)
    return frozenset(stem for stem in states.keys() | maps.keys() if any(states.get(leaf) in {"rejected", "abandoned"} for leaf in successor_leaves(stem, maps)))


async def record_supersedes(ctx: StageContext, order: ReworkOrder) -> list[Finding]:
    """The lock-owning publisher calls this AFTER committing all reviewed split proposals."""
    if order.action != "split":
        return []
    successors = tuple(sorted(t.stem for t in order.tickets))
    maps = supersedes_maps(ctx.driver.journal.read())
    road = "retain the recorded map; author fresh, acyclic successors and commit every reviewed ticket first"
    if order.stem in maps:
        return [] if maps[order.stem] == successors else [_finding("supersedes map cannot replace an existing map", road)]
    if not successors or len(successors) != len(set(successors)) or order.stem in successors or any(order.stem in successor_leaves(s, maps) for s in successors):
        return [_finding("supersedes map would close a cycle or self-edge", road)]
    for proposal in order.tickets:
        if errors := stem_findings(proposal.stem):
            return errors
        path = ticket_path(proposal.stem)
        try:
            committed = await ctx.git._run(ctx.repo, "show", f"HEAD:{path}")
        except GitError:
            return [_finding(f"successor {proposal.stem!r} is not committed", road, path=path)]
        if committed != proposal.ticket:
            return [_finding(f"committed successor {proposal.stem!r} differs from its reviewed proposal", "commit the exact reviewed proposal before recording supersession", path=path)]
    ctx.driver.journal.append(EventType.SIGNAL, {"signal": SUPERSEDES, "successors": list(successors)}, ticket=order.stem, key=None)
    return []
