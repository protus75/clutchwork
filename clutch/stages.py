"""The Implement, Check, and Review stages.

Implement and Review are prompt specs run through the one driver; Check is mechanical. This module
owns stage-evidence gathering and the stage-terminal OUTBOX lift: each
stage writes its artifact into `tickets/<stem>/` inside the worktree, and at the stage terminal the
lift moves it to the canonical tickets dir as ONE ticket-plane commit `clutch(<stem>): <kind>`.

The run's terminal `state_transition` is not written here: that is the runner's.
"""

import ast
import asyncio
import fnmatch
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, Field, TypeAdapter, model_validator

from clutch import git, images, meta, visual
from clutch.artifacts import (
    OUTCOMES,
    REVIEW_BASELINE_REPORT,
    Artifact,
    Cost,
    Diagnosis,
    DiagnosisReply,
    Finding,
    FrozenModel,
    Harvest,
    NonBlank,
    Outcome,
    ReviewBaselineReport,
    ReviewVerdict,
    StageResult,
    major,
    refused,
)
from clutch.baseline import resolve_visual_baseline
from clutch.config import Config, ConfigSnapshot, Severity
from clutch.context import hint_block
from clutch.driver import Driver, LlmStage
from clutch.enginelog import engine_log_path
from clutch.gates import BugEvidence, GateReport, RegressionRun, run_gates
from clutch.git import Git, GitError
from clutch.hostfiles import CORE_TEMPLATE, CoreDriftGate, committed_core
from clutch.journal import EventType, last_transition, run_seq
from clutch.journal import run_seq as journal_run_seq
from clutch.llmeffect import llm_key, scoped_seq
from clutch.panel import DIAGNOSIS_ORDER, PanelMember, findings_union, majority_verdict
from clutch.providers import ProviderSetupError, child_env, panel_members
from clutch.seams import ExecutableNotFound, FileSystem, ProcessExec
from clutch.specs import RENDER_BOUND_CHARS, RenderOverBound, Spec, load_spec, render
from clutch.storm import arrival_id
from clutch.tickets import (
    _HEADING,
    CHECKS_FILE,
    DIAGNOSIS_FILE,
    REVIEW_FILE,
    RUN_FILE,
    TEST_FIXTURE_DIRS,
    TICKET_FILE,
    TICKETS_DIR,
    Ticket,
    _criteria,
    artifact_path,
    context_excerpt,
    context_path,
    harvest_path,
    in_fence,
    parse_render,
    ticket_path,
)
from clutch.tickets import validate_ticket as validate_ticket

HOST_COMMAND_LOCK = asyncio.Semaphore(1)

MAIN = "main"
LIFT_MAX_BYTES = 256 * 1024
KNOWN_ARTIFACTS: Mapping[str, type[BaseModel]] = {
    REVIEW_BASELINE_REPORT: ReviewBaselineReport,
}
# Diff budget: sized so every rendered review prompt fits the serving provider's bound.
DIFF_BUDGET_INSERTED = 1_500
# The mechanical Check has no prompt spec; this versions its own contract in the provenance slot.
CHECK_SPEC_VERSION = 1
OUTPUT_TAIL_CHARS = 2_000
RUN_RECORD_SECTIONS = (
    "Outcome",
    "Surprises / judgment calls",
    "Dead ends",
    "Second problems filed",
    "Resolved engine/model",
    "Predicted vs actual",
)

StageName = Literal["implement", "check", "review"]
# The attempt-scoped re-entry block's heading, rendered in criteria-position.
PRIOR_ATTEMPTS = "## Prior attempts (attempt-scoped, informational, unverified, not reviewed)"
DIAGNOSIS_STUCK_S = 600.0


# --- artifacts ----------------------------------------------------------------------------------


class SecondProblem(FrozenModel):
    summary: NonBlank


class ImplementReply(FrozenModel):
    """The implement surface's model-facing reply (clutch/specs/implement.md); the stage stamps provenance."""

    outcome: Literal["ok", "already_satisfied", "premise_failed", "incomplete"]
    summary: NonBlank
    surprises: str
    dead_ends: str
    predicted_vs_actual: str
    findings: list[Finding]
    second_problems: list[SecondProblem] = []

    @model_validator(mode="after")
    def _findings_match_outcome(self) -> "ImplementReply":
        if self.outcome == "premise_failed":
            if not self.findings or any(f.code != "premise" or not f.path or not f.path.strip() for f in self.findings):
                raise ValueError(
                    "premise_failed needs at least one finding, every code `premise` and every one naming `path` "
                    "(the file outside the fence, the file the criteria contradict, or the ticket); unfinished or large "
                    "work is not a premise failure: implement the ticket and reply ok, or reply incomplete when you stopped before finishing"
                )
        elif self.findings:
            raise ValueError(f"{self.outcome} carries an empty findings list; reply premise_failed for a ticket defect or incomplete for unfinished work")
        return self


class PackingSlip(Artifact):
    """Implement's artifact: the branch plus its run record."""

    stem: NonBlank
    branch: NonBlank
    outcome: Literal["ok", "already_satisfied"]
    summary: NonBlank
    run_record: NonBlank  # repo-relative path of the lifted run.md


class SeedReview(FrozenModel):
    """The Check verdict for one authored seed, pinned to its ticket.md blob."""

    stem: NonBlank
    ticket_sha: NonBlank
    verdict: Literal["approve", "snag", "rma"]
    findings: list[Finding]
    mechanical: str | None


class Invoice(Artifact):
    """Check's artifact, persisted as `checks.json`: every mechanical gate report for one branch head."""

    stem: NonBlank
    passed: bool
    changed_files: list[str]
    inserted_lines: Annotated[int, Field(ge=0)]
    bypassed: list[str]  # gate codes the ticket's `gate_bypass` valve demoted to soft
    reports: list[GateReport]
    # Historical checks.json files contain seed reviews; retro and triage parse them through Invoice.
    seeds: list[SeedReview] = []
    verification: list["CommandResult"] = []


class _Review(Artifact):
    stem: NonBlank
    reviewed_sha: NonBlank
    summary: NonBlank
    findings: list[Finding]
    spec_version: NonBlank
    provider: str | None
    model: str | None


class ApprovedInvoice(_Review):
    verdict: Literal["approve"]


class SnagList(_Review):
    verdict: Literal["snag"]


class Rma(_Review):
    verdict: Literal["rma"]


ReviewArtifact = Annotated[ApprovedInvoice | SnagList | Rma, Field(discriminator="verdict")]
EMITS_BY_VERDICT: Mapping[str, type[_Review]] = {"approve": ApprovedInvoice, "snag": SnagList, "rma": Rma}
_REVIEW = TypeAdapter(ReviewArtifact)
_REVIEW_JSON = re.compile(r"^```json\n(.*?)\n```$", re.DOTALL | re.MULTILINE)


def render_review(review: _Review) -> str:
    lines = [f"# Review: {review.verdict}", "", review.summary, "", "## Findings", ""]
    lines += [f"- [{f.code}] {f.path or '-'}:{f.line or '-'} {f.message} (do instead: {f.paved_road})" for f in review.findings] or ["none"]
    return "\n".join(lines + ["", "## Record", "", "```json", review.model_dump_json(indent=2), "```", ""])


def read_review(text: str) -> ApprovedInvoice | SnagList | Rma:
    """Parse `review.md`'s pinned record (the merge gate's on-disk input); the prose above it is not read."""
    m = _REVIEW_JSON.search(text)
    if m is None:
        raise ValueError("review.md carries no ```json record block; re-run Review to rewrite it")
    return _REVIEW.validate_json(m.group(1))


async def served_review(ctx, stem: str, attempt: int, reviewed: str) -> tuple[str | None, str | None]:
    """Only the approving call and its committed lift can attest to the served pair."""
    from clutch.driver import unwrap_fence

    events = ctx.driver.journal.read()
    path = artifact_path(stem, REVIEW_FILE)
    lifts = ctx.driver.effects.recorded(f"ticket-plane/{stem}/{attempt}/review", ticket=stem)
    if len(lifts) != 1 or lifts[0]["kind"] != "review" or path not in lifts[0]["paths"]:
        return None, None
    commit = lifts[0]["commit"]
    pinned = await ctx.git._run(ctx.repo, "show", f"{MAIN}:{path}")
    if await ctx.git.merge_base(ctx.repo, MAIN, commit) != commit or pinned != await ctx.git._run(ctx.repo, "show", f"{commit}:{path}"):
        return None, None
    review = read_review(pinned)
    if not isinstance(review, ApprovedInvoice) or review.stem != stem or review.reviewed_sha != reviewed:
        return None, None
    calls = [e for e in events if e.type == EventType.EFFECT_COMPLETION and e.ticket == stem and e.key and re.fullmatch(rf"llm/{re.escape(stem)}/{attempt}/review/{attempt}/[1-9][0-9]*", e.key)]
    if not calls:
        return None, None
    call = calls[-1]
    if any(e.key == call.key and e.body != call.body for e in calls):
        return None, None
    result = call.body["result"]
    verdict = ReviewVerdict.model_validate_json(unwrap_fence(result["text"]))
    pair = result["provider"], result["model"]
    if (
        verdict.verdict != "approve"
        or verdict.summary != review.summary
        or verdict.findings != review.findings
        or pair != (review.provider, review.model)
        or any(not isinstance(n, str) or not n.strip() for n in pair)
        or any(call.body["cost"].get(k) != result[k] for k in ("provider", "model"))
    ):
        return None, None
    return pair


# --- context ------------------------------------------------------------------------------------


@dataclass
class StageBoundary:
    """Memory-only selection supplied by the lifetime; bootstrap has no suspension policy."""

    select: Callable[[Ticket, StageName], bool] | None = None
    run: "StagesRun | None" = None
    ticket: Ticket | None = None
    next_stage: StageName | None = None
    active: asyncio.Task | None = None


@dataclass(frozen=True)
class StageContext:
    """The seams one ticket run's stages share. `env` is the parent env; children get it minus secrets."""

    repo: Path
    config: Config | ConfigSnapshot
    env: Mapping[str, str]
    exec_: ProcessExec
    git: Git
    fs: FileSystem
    driver: Driver
    specs_dir: Path
    boundary: StageBoundary = field(default_factory=StageBoundary, init=False, compare=False)

    def worktree(self, stem: str) -> Path:
        assert self.config.worktree_root is not None  # resolved at config load
        return self.config.worktree_root / stem

    async def abort_current(self) -> None:
        from clutch.daemon import _protected_cleanup

        try:
            await self.driver.abort_current()
        finally:
            task = self.boundary.active
            if task is not None:
                if not task.done() and not task.cancelling():
                    task.cancel()
                cleanup = asyncio.gather(task, return_exceptions=True)
                await _protected_cleanup(cleanup)
                [result] = cleanup.result()
                if isinstance(result, BaseException) and not isinstance(result, asyncio.CancelledError):
                    raise result


async def ticket_change_findings(ctx: StageContext, stem: str, *, expected: str | None = None) -> list[Finding]:
    """Only ticket.md belongs to the dispatch identity; lifts may freely move main."""
    if expected is None:
        latest = last_transition(ctx.driver.journal.read(), stem) or {}
        if latest.get("to") == "running":
            expected = latest.get("ticket_sha")
    if expected is None:
        return []
    rel = ticket_path(stem)
    try:
        committed = await ctx.git.rev_parse(ctx.repo, f"{MAIN}:{rel}")
        unchanged = committed == expected and git.blob_sha((ctx.repo / rel).read_bytes()) == expected
    except GitError, OSError:
        unchanged = False
    if unchanged:
        return []
    return [
        Finding(
            code="ticket_changed",
            path=rel,
            message=f"{stem}: ticket.md changed during the run",
            paved_road=f"review the change to {rel}, then keep (`clutch ticket confirm {stem}`) or kill (`clutch ticket reject {stem}`)",
        )
    ]


class ArtifactInvalid(Exception):
    def __init__(self, path: Path, error: Exception) -> None:
        super().__init__(f"{path}: {error}")
        self.path = path
        self.error = error


class Stages:
    """Public access to the Driver already owned by the stage composition."""

    def __init__(self, ctx: StageContext):
        self._ctx = ctx

    @property
    def driver(self) -> Driver:
        return self._ctx.driver


def _registered_files(outbox: Path) -> list[Path]:
    return [p for p in outbox.rglob("*") if p.is_file() and p.name in KNOWN_ARTIFACTS]


def _lift_decision(kind: str, only: str | None, rel: str, is_symlink: bool, size: int) -> Literal["skip", "lift", "too_large"]:
    if is_symlink:
        return "skip"
    if only is not None:
        selected = rel == only
    else:
        selected = (kind == "run-record" and rel == RUN_FILE) or (kind == "review" and rel == REVIEW_FILE) or (kind == "checks" and (rel == CHECKS_FILE or Path(rel).name in KNOWN_ARTIFACTS))
    if not selected:
        return "skip"
    return "too_large" if size > LIFT_MAX_BYTES else "lift"


def _lift_files(ctx: StageContext, stem: str, kind: str, only: str | None = None) -> list[Path]:
    outbox = ctx.worktree(stem) / TICKETS_DIR / stem
    canonical = ctx.repo / TICKETS_DIR / stem
    files = []
    for p in outbox.rglob("*"):
        if not (p.is_symlink() or p.is_file()):
            continue
        rel = p.relative_to(outbox)
        if rel == Path(TICKET_FILE):
            continue
        size = p.lstat().st_size
        decision = _lift_decision(kind, only, rel.as_posix(), p.is_symlink(), size)
        if decision == "too_large":
            raise ArtifactInvalid(p, ValueError(f"artifact is {size} bytes, over the {LIFT_MAX_BYTES}-byte lift limit"))
        if decision == "lift" and not ((c := canonical / rel).is_file() and c.read_bytes() == p.read_bytes()):
            files.append(p)
    return sorted(files)


def _validate_reports(paths: Sequence[Path]) -> None:
    for path in paths:
        if path.name in KNOWN_ARTIFACTS:
            try:
                KNOWN_ARTIFACTS[path.name].model_validate_json(path.read_bytes())
            except Exception as error:
                raise ArtifactInvalid(path, error) from error


async def dirty_code(ctx: StageContext, stem: str) -> list[str]:
    # NUL records preserve filenames and include both sides of a staged rename.
    records = iter((await ctx.git.status_porcelain(ctx.worktree(stem), "--untracked-files=all", "-z")).rstrip("\0").split("\0"))
    paths = []
    for record in records:
        if not record:
            continue
        paths.append(record[3:])
        if "R" in record[:2] or "C" in record[:2]:
            paths.append(next(records))
    outbox = f"{TICKETS_DIR}/{stem}/"
    return [p for p in paths if not p.startswith(outbox) or p == outbox + TICKET_FILE]


def _spec(ctx: StageContext, surface: str) -> Spec:
    return load_spec((ctx.specs_dir / f"{surface}.md").read_text())


def _major(spec: Spec) -> int:
    return major(spec.meta.version)


def findings_text(findings: Sequence[Finding]) -> str:
    return "\n".join(f"- {f.code}: {f.message} (do instead: {f.paved_road})" for f in findings) or "none"


@dataclass(frozen=True)
class DiagnosisMaterial:
    ticket: str
    terminal: str
    stage: str | None
    harvest: Harvest | None
    run_record: str | None


def diagnose_stage(spec: Spec, material: DiagnosisMaterial) -> LlmStage:
    """The one pure diagnosis render, shared with the real-model evaluation."""
    inputs = {
        "ticket": material.ticket,
        "terminal": f"{material.terminal} at {material.stage or 'none'}",
        "harvest": material.harvest.model_dump_json() if material.harvest else "none",
        "run_record": material.run_record or "none",
    }

    def render_material(_: DiagnosisMaterial, findings: list[Finding]) -> str:
        return render(spec, {**inputs, "retry_findings": findings_text(findings)})

    return LlmStage(surface="diagnose", emits=DiagnosisReply, gates=[], render=render_material)


async def write_diagnosis(
    ctx: StageContext,
    ticket: Ticket,
    *,
    attempt: int,
    terminal: str,
    stage: str | None,
    verdict: str,
    lessons: list[str],
    mechanical: str | None,
    cost: Cost = Cost(),
    trimmed_lessons: list[int] | None = None,
) -> Diagnosis:
    spec = _spec(ctx, "diagnose")
    record = Diagnosis(
        produced_by_spec_version=_major(spec),
        produced_at_sha=await ctx.git.rev_parse(ctx.repo, ticket.stem),
        stem=ticket.stem,
        attempt=attempt,
        terminal=terminal,
        stage=stage,
        verdict=verdict,
        lessons=lessons,
        mechanical=mechanical,
        trimmed_lessons=trimmed_lessons if trimmed_lessons is not None else [],
        spec_version=spec.meta.version,
        provider=cost.provider,
        model=cost.model,
    )
    ctx.fs.write(ctx.worktree(ticket.stem) / artifact_path(ticket.stem, DIAGNOSIS_FILE), (record.model_dump_json(indent=2) + "\n").encode())
    await lift_outbox(ctx, ticket.stem, "diagnosis", attempt=attempt, only=DIAGNOSIS_FILE)
    return record


def _panel_combine(panel, selected):
    replies = [member.artifact for member in panel.members]
    indexes = [i for i in range(len(selected)) if i not in {d.index for d in panel.dropped}]
    members = [
        PanelMember(provider=member.cost.provider or selected[index].provider.name, model=member.cost.model or selected[index].model, verdict=reply.verdict)
        for member, reply, index in zip(panel.members, replies, indexes, strict=False)
    ]
    costs = [member.cost for member in panel.members]
    cost = Cost(
        tokens=sum(c.tokens for c in costs) if all(c.tokens is not None for c in costs) else None,
        seconds=sum(c.seconds for c in costs),
        attempts=sum(c.attempts for c in costs),
        usd=sum(c.usd for c in costs),
        provider=costs[0].provider,
        model=costs[0].model,
    )
    return replies, members, cost


async def diagnose(ctx: StageContext, ticket: Ticket, material: DiagnosisMaterial, *, attempt: int) -> Diagnosis:
    spec = _spec(ctx, "diagnose")
    stage = diagnose_stage(spec, material)
    try:
        selected = panel_members(ctx.config, ticket.frontmatter.agent_tier, "diagnose", ticket.frontmatter.kind)
    except ProviderSetupError:
        selected = ()
    size = len(selected) or 1
    kwargs = dict(
        ticket=ticket.stem,
        kind=ticket.frontmatter.kind,
        attempt=attempt,
        workspace=ctx.worktree(ticket.stem),
        tier=ticket.frontmatter.agent_tier,
        effort=ticket.frontmatter.agent_effort,
        stuck_budget=DIAGNOSIS_STUCK_S,
        expected_budget=ticket.expected_minutes * 60.0,
        scope_fence=(),
    )
    if size == 1:
        result = await ctx.driver.run(stage, material, **kwargs)
    else:
        panel = await ctx.driver.run_panel(stage, material, size=size, **kwargs)
        if not panel.members:
            result = StageResult("infra_error", None, [], Cost())
        elif bad := next((member for member in panel.members if member.outcome != "ok"), None):
            result = bad
        else:
            replies, members, cost = _panel_combine(panel, selected)
            assert all(isinstance(reply, DiagnosisReply) for reply in replies)
            reply, facts = majority_verdict(replies, DIAGNOSIS_ORDER, members, panel.dropped)
            winner = next(i for i, candidate in enumerate(replies) if candidate is reply)
            cost = Cost(tokens=cost.tokens, seconds=cost.seconds, attempts=cost.attempts, usd=cost.usd, provider=members[winner].provider, model=members[winner].model)
            result = StageResult("ok", reply, [], cost)
            ctx.driver.journal.append(EventType.SIGNAL, {"signal": "panel_facts", "attempt": attempt, "surface": "diagnose", **facts.model_dump()}, ticket=ticket.stem)
    reply = result.artifact
    if result.outcome == "ok" and isinstance(reply, DiagnosisReply):
        return await write_diagnosis(
            ctx,
            ticket,
            attempt=attempt,
            terminal=material.terminal,
            stage=material.stage,
            verdict=reply.verdict,
            lessons=list(reply.lessons),
            mechanical=None,
            cost=result.cost,
            trimmed_lessons=reply.trimmed_lessons,
        )
    return await write_diagnosis(
        ctx, ticket, attempt=attempt, terminal=material.terminal, stage=material.stage, verdict="abandon-human", lessons=[], mechanical=f"no schema-valid verdict ({result.outcome})", cost=result.cost
    )


def _short(result: StageResult, outcome: Outcome, findings: list[Finding], artifact: Artifact | None = None) -> StageResult:
    return StageResult(outcome=outcome, artifact=artifact, findings=findings, cost=result.cost)


async def prepare_worktree(ctx: StageContext, stem: str, *, keep: bool = False) -> Path:
    """Reuse a failed branch when requested, otherwise create a fresh branch from main."""
    path = ctx.worktree(stem)
    if path.exists():
        await ctx.git.worktree_remove(ctx.repo, path)
    else:
        await ctx.git.worktree_prune(ctx.repo)
    try:
        await ctx.git.rev_parse(ctx.repo, f"refs/heads/{stem}")
    except GitError:
        pass  # no leftover branch
    else:
        if keep:
            ctx.fs.mkdir(path.parent)
            await ctx.git.worktree_attach(ctx.repo, path, stem)
            try:
                await ctx.git.rebase(path, MAIN)
            except GitError:
                await ctx.git.worktree_remove(ctx.repo, path)
            else:
                return path
        await ctx.git.branch_delete(ctx.repo, stem)
    ctx.fs.mkdir(path.parent)
    await ctx.git.worktree_add(ctx.repo, path, stem, MAIN)
    return path


async def _base_worktree(ctx: StageContext, kind: str, stem: str, base: str) -> Path:
    assert ctx.config.worktree_root is not None  # resolved at config load
    path = ctx.config.worktree_root / kind / stem
    if path.exists():
        await ctx.git.worktree_remove(ctx.repo, path)
    ctx.fs.mkdir(path.parent)
    await ctx.git.worktree_add_detached(ctx.repo, path, base)
    return path


async def lift_outbox(ctx: StageContext, stem: str, kind: str, *, attempt: int, only: str | None = None, key_scope: str | None = None) -> str | None:
    """Move the worktree outbox into the canonical ticket dir as ONE ticket-plane commit; None if empty.

    `ticket.md` is never lifted: it stays read-only to the agent. Keyed with the run
    sequence, so a same-run re-entry never commits twice. A file byte-equal to its canonical copy is a prior
    run's artifact the worktree inherited from main, not this stage's output: it is never lifted.
    """
    outbox = ctx.worktree(stem) / TICKETS_DIR / stem
    files = _lift_files(ctx, stem, kind, only)
    if not files:
        return None
    _validate_reports(files)

    async def commit() -> dict:
        rels = []
        for src in files:
            rel = f"{TICKETS_DIR}/{stem}/{src.relative_to(outbox).as_posix()}"
            ctx.fs.write(ctx.repo / rel, src.read_bytes())
            ctx.fs.remove(src)
            rels.append(rel)
        sha = await ctx.git.commit(ctx.repo, f"clutch({stem}): {kind}", only=rels)
        return {"kind": kind, "paths": rels, "commit": sha}

    key = "/".join(("ticket-plane", stem, str(scoped_seq(key_scope, attempt)), kind))
    return (await ctx.driver.effects.run(commit, key=key, ticket=stem))["commit"]


async def lift_prior_diff(ctx: StageContext, stem: str, *, attempt: int, diff: str, conflicted: list[str]) -> str | None:
    """Commit the discarded diff's non-conflicting file sections to the ticket plane."""
    sections = re.split(r"(?=^diff --git )", diff, flags=re.MULTILINE)
    kept = []
    for section in sections:
        if not section.startswith("diff --git "):
            continue
        header = section.splitlines()[0][len("diff --git ") :]
        # Git quotes unusual paths as C-style strings; ordinary paths may contain spaces.
        match = re.fullmatch(r'("(?:[^"\\]|\\.)*"|a/.*?) ("(?:[^"\\]|\\.)*"|b/.*)', header)
        if not match:
            raise ValueError(f"invalid diff header: {header}")
        paths = []
        for name in match.groups():
            if name.startswith('"'):
                name = ast.literal_eval("b" + name).decode("utf-8")
            paths.append(name[2:])
        if not any(path in conflicted for path in paths):
            kept.append(section)
    if not kept:
        return None
    rel = f"{TICKETS_DIR}/{stem}/attempts/{attempt}/prior.diff"

    async def commit() -> dict:
        ctx.fs.write(ctx.repo / rel, "".join(kept).encode())
        sha = await ctx.git.commit(ctx.repo, f"clutch({stem}): prior-diff", only=[rel])
        return {"kind": "prior-diff", "paths": [rel], "commit": sha}

    return (await ctx.driver.effects.run(commit, key=f"ticket-plane/{stem}/{attempt}/prior-diff", ticket=stem))["commit"]


# --- Implement ----------------------------------------------------------------------------------


def implement_inputs(repo: Path, ticket_text: str, ticket: Ticket, context_files: Sequence[Path], *, related_files: str = "none") -> dict[str, str]:
    """The production Implement inputs, also used to measure a ticket at authoring."""
    paths = list(dict.fromkeys([*ticket.context, *(str(p) for p in context_files)]))
    entries = []
    for p in paths:
        if p in ticket.context:
            text = (repo / context_path(p)).read_text()
            try:
                body = context_excerpt(p, text)
            except ValueError as exc:
                body = f"(selector does not resolve in this worktree: {exc}; read the file directly)"
        else:
            body = (repo / p).read_text()
        entries.append(f"### {p}\n{body}")
    context = "\n\n".join(entries) or "none"
    return {
        "ticket": ticket_text,
        "context": context,
        "related_files": related_files,
    }


HINT_TIMEOUT_S = 5.0
HINT_HEADROOM_CHARS = 50_000


async def related_files(config, ticket, *, hint=hint_block) -> str:
    try:
        if not config.index.implement_hint:
            return "none"
        text = ticket.sections["Goal / Why"] + "\n" + ticket.sections.get("Scope in / Scope out", "")
        return await asyncio.wait_for(asyncio.to_thread(hint, config.state_dir, ticket.stem, list(ticket.scope_fence), list(ticket.context), text), HINT_TIMEOUT_S)
    except TimeoutError:
        return "unavailable: timeout"
    except Exception:
        return "unavailable: index_unreadable"


def _one_line(text: str) -> str:
    # A payload newline could forge a ticket section heading inside the rendered ticket block.
    return " ".join(text.split())


def _prior_findings(ctx: StageContext, stem: str, stage: str | None) -> list[Finding]:
    """The terminal stage's durable findings artifact in the canonical ticket dir; [] when it wrote none."""
    if stage == "review" and (path := ctx.repo / artifact_path(stem, REVIEW_FILE)).is_file():
        return list(read_review(path.read_text()).findings)
    if stage == "check" and (path := ctx.repo / artifact_path(stem, CHECKS_FILE)).is_file():
        invoice = Invoice.model_validate_json(path.read_text())
        return [f for r in invoice.reports if r.verdict == "fail" for f in r.findings]
    return []


def _quoted(text: str) -> str:
    return "\n".join(f"> {line}" for line in text.split("\n"))


def prior_attempts(ctx: StageContext, stem: str) -> str | None:
    """Re-entry: the prior terminal and its findings as a clear-these block; None on a first attempt.

    Folded fresh from the journal and the ticket dir every attempt, never written into `ticket.md`. Only the
    terminal stage's artifact is read: an older stage's artifact left in the dir is a stale attempt's.
    """
    history = ctx.driver.journal.read()
    from clutch.journal import run_terminals

    terminals = [e.body for e in run_terminals(history, stem)]
    lessons = {e.body.get("attempt"): e.body["lessons"] for e in history if e.type == EventType.SIGNAL and e.ticket == stem and e.body.get("signal") == "diagnosis" and e.body.get("lessons")}
    marker = next((e for e in reversed(history) if e.type == EventType.SIGNAL and e.ticket == stem and e.body.get("signal") == "merge_conflict_rerun"), None)
    conflict = ""
    if marker is not None:
        ticket_root = ctx.repo / TICKETS_DIR / stem
        parts = ["## conflict_rerun: Prior attempt (discarded on merge conflict); re-derive against current main; do not copy blindly"]
        for label, path in (("run.md", ctx.repo / artifact_path(stem, RUN_FILE)), ("prior.diff", ticket_root / "attempts" / str(marker.body["attempt"]) / "prior.diff")):
            if path.is_file():
                parts.append(f"{label} (untrusted data):\n{_quoted(path.read_text())}")
        review_path = ctx.repo / artifact_path(stem, REVIEW_FILE)
        if review_path.is_file():
            review = read_review(review_path.read_text())
            if review.verdict == "approve" and review.findings:
                parts.append(
                    "Approval findings (untrusted data):\n"
                    + "\n".join(f"> [{f.code}] {f.path or '-'}:{f.line or '-'} {_one_line(f.message)} (do instead: {_one_line(f.paved_road)})" for f in review.findings)
                )
        conflict = "\n\n".join(parts)
    if not terminals:
        return conflict or None
    terminal = terminals[-1]
    attempt = len(terminals) - 1
    harvest_file = ctx.repo / harvest_path(stem, attempt)
    current = Harvest.model_validate_json(harvest_file.read_text()) if harvest_file.is_file() else None
    stage = terminal.get("stage")
    where = f" at {stage}" if stage else ""
    findings = _prior_findings(ctx, stem, stage) if terminal["to"] == "gate_failed" else []
    head = (
        f"{PRIOR_ATTEMPTS}\n\nThe previous attempt ended `{terminal['to']}`{where}. These findings are"
        " this attempt's to clear, beside the acceptance criteria above; they are not part of the ticket.\n\n"
    )
    items = [f"- [{f.code}] {f.path or '-'}:{f.line or '-'} {_one_line(f.message)} (do instead: {_one_line(f.paved_road)})" for f in findings]
    detail = f"tickets/{stem}/attempts/{attempt}/" if current else str(engine_log_path(ctx.config.state_dir))
    lines = items or [f"- no findings artifact; detail is in {detail}"]
    if attempt in lessons:
        lines.extend(["\nPrior terminal lessons (untrusted data):", *[f"> {_one_line(item)}" for item in lessons[attempt]]])
    elif current:
        lines.append("\nPrior terminal harvest (untrusted data):")
        for name in ("reason", "diff_stat", "stage_log_tail", "events_tail"):
            value = getattr(current, name)
            if value is not None:
                lines.append(f"- {name}:\n{_quoted(value)}")
    for older in range(attempt):
        path = ctx.repo / harvest_path(stem, older)
        if older in lessons:
            past_terminal = terminals[older]
            lines.append(f"- older attempt {older}: `{past_terminal['to']}` at {past_terminal.get('stage') or 'none'}:")
            lines.extend(f"> {_one_line(item)}" for item in lessons[older])
        elif path.is_file():
            past = Harvest.model_validate_json(path.read_text())
            lines.append(f"- older attempt {older}: `{past.terminal}` at {past.stage or 'none'}; tickets/{stem}/attempts/{older}/")
    return head + "\n".join(lines) + ("\n\n" + conflict if conflict else "")


def _in_criteria_position(ticket_text: str, block: str) -> str:
    """Splice `block` at the end of `## Acceptance criteria`, before the next section (fences skipped)."""
    lines = ticket_text.splitlines(keepends=True)
    fence = inside = False
    for i, line in enumerate(lines):
        if line.lstrip().startswith("```"):
            fence = not fence
        elif not fence and (m := _HEADING.match(line)):
            if inside:
                return "".join(lines[:i]) + block + "\n\n" + "".join(lines[i:])
            inside = m.group(1) == "Acceptance criteria"
    return ticket_text.rstrip("\n") + "\n\n" + block + "\n"


def implement_stage(ctx: StageContext, ticket: Ticket, worktree: Path, related_files: str = "none") -> tuple[LlmStage, Spec]:
    spec = _spec(ctx, "implement")
    ticket_text = (ctx.repo / ticket_path(ticket.stem)).read_text()
    if (prior := prior_attempts(ctx, ticket.stem)) is not None:
        ticket_text = _in_criteria_position(ticket_text, prior)
    inputs = implement_inputs(worktree, ticket_text, ticket, ctx.config.context_files, related_files=related_files)
    if len(inputs["ticket"]) + len(inputs["context"]) > RENDER_BOUND_CHARS - HINT_HEADROOM_CHARS:
        inputs["related_files"] = "none"

    def render_ticket(_: Ticket, findings: list[Finding]) -> str:
        return render(spec, {**inputs, "retry_findings": findings_text(findings)})

    return LlmStage(surface="implement", emits=ImplementReply, gates=[], render=render_ticket), spec


def run_record(reply: ImplementReply | None, cost: Cost, spec: Spec, second_problem_ids: Sequence[str], *, outcome: Outcome | None = None) -> str:
    fields = {
        "Outcome": outcome or reply.outcome,
        "Surprises / judgment calls": reply.surprises if reply else "none",
        "Dead ends": reply.dead_ends if reply else "none",
        "Second problems filed": "\n".join(f"- {id}: {_one_line(problem.summary)}" for id, problem in zip(second_problem_ids, reply.second_problems if reply else (), strict=True)) or "none",
        "Resolved engine/model": f"- provider: {cost.provider}\n- model: {cost.model}\n- spec: {spec.meta.llm_surface} {spec.meta.version}",
        "Predicted vs actual": reply.predicted_vs_actual if reply else "none",
    }
    return "".join(f"## {name}\n\n{(fields[name].strip() or 'none')}\n\n" for name in RUN_RECORD_SECTIONS)


async def implement(ctx: StageContext, ticket: Ticket, *, attempt: int) -> StageResult:
    """Prepare the worktree, run the implement spec in it, and write + lift the run record."""
    stem = ticket.stem
    from clutch.journal import run_terminals

    history = ctx.driver.journal.read()
    terminals = run_terminals(history, stem)
    terminal = terminals[-1] if terminals else None
    keep = bool(terminal and terminal.body.get("to") == "gate_failed" and terminal.body.get("stage") in {"check", "review"})
    if keep:
        after_terminal = history[next(i for i, event in enumerate(history) if event is terminal) + 1 :]
        keep = not any(e.type == EventType.SIGNAL and e.ticket == stem and e.body.get("signal") == "merge_conflict_rerun" for e in after_terminal)
    worktree = await prepare_worktree(ctx, stem, keep=keep)
    no_room = False
    try:
        if ctx.config.index.implement_hint:
            ticket_text = (ctx.repo / ticket_path(stem)).read_text()
            if (prior := prior_attempts(ctx, stem)) is not None:
                ticket_text = _in_criteria_position(ticket_text, prior)
            inputs = implement_inputs(worktree, ticket_text, ticket, ctx.config.context_files)
            no_room = len(inputs["ticket"]) + len(inputs["context"]) > RENDER_BOUND_CHARS - HINT_HEADROOM_CHARS
    except Exception:
        pass  # The normal stage construction retains responsibility for input failures.
    related = "none" if no_room else await related_files(ctx.config, ticket)
    stage, spec = implement_stage(ctx, ticket, worktree, related)
    try:
        result = await ctx.driver.run(
            stage,
            ticket,
            ticket=stem,
            kind=ticket.frontmatter.kind,
            attempt=attempt,
            workspace=worktree,
            tier=ticket.frontmatter.agent_tier,
            effort=ticket.frontmatter.agent_effort,
            stuck_budget=ticket.stuck_minutes * 60.0,
            expected_budget=ticket.expected_minutes * 60.0,
            scope_fence=ticket.scope_fence,
        )
    except RenderOverBound as e:
        # The pre-call short-circuit: ticket-text arithmetic, parked like premise_failed.
        return StageResult(outcome="premise_failed", artifact=None, findings=[e.finding], cost=Cost())
    if result.outcome != "ok":
        if result.cost.provider is not None:
            record = artifact_path(stem, RUN_FILE)
            ctx.fs.write(worktree / record, run_record(None, result.cost, spec, [], outcome=result.outcome).encode())
            await lift_outbox(ctx, stem, "run-record", attempt=attempt)
        return result
    reply = result.artifact
    assert isinstance(reply, ImplementReply)
    from clutch.daemon import storm_producer_for_config

    box = storm_producer_for_config(ctx.config, fs=ctx.fs, journal=ctx.driver.journal, clock=ctx.driver.clock)
    second_problem_ids = [
        box.enqueue(message_class="suggestion", origin=stem, stage="implement", outcome=reply.outcome, summary=problem.summary, occurrence_id=arrival_id("second-problem", stem, attempt, index))[0]
        for index, problem in enumerate(reply.second_problems)
    ]
    record = artifact_path(stem, RUN_FILE)
    ctx.fs.write(worktree / record, run_record(reply, result.cost, spec, second_problem_ids).encode())
    await lift_outbox(ctx, stem, "run-record", attempt=attempt)
    if reply.outcome in ("premise_failed", "incomplete"):
        return _short(result, reply.outcome, list(reply.findings))
    slip = PackingSlip(
        produced_by_spec_version=_major(spec),
        produced_at_sha=await ctx.git.rev_parse(ctx.repo, stem),
        stem=stem,
        branch=stem,
        outcome=reply.outcome,
        summary=reply.summary,
        run_record=record,
    )
    return _short(result, "ok", [], slip)


# --- Check --------------------------------------------------------------------------------------


class CommandResult(FrozenModel):
    argv: list[str]
    rc: int | None  # None: the command could not run or timed out -- fails closed like a nonzero exit
    tail: str
    base_red: bool = False
    seconds: float | None = None


async def run_host_command(ctx, ticket, attempt, argv, code, name, *, cwd=None, stdout_capture=None):
    road = "make the configured command exit 0 on the rebased candidate and retry"
    started = ctx.driver.clock()
    env = child_env(ctx.env, ctx.config)
    engine_bin = str(Path(sys.executable).parent)
    env["PATH"] = engine_bin + os.pathsep + env["PATH"] if env.get("PATH") else engine_bin
    try:
        async with HOST_COMMAND_LOCK:
            rc, out, err = await ctx.exec_.run(argv, cwd=cwd or ctx.worktree(ticket.stem), env=env, timeout=ticket.stuck_minutes * 60.0)
    except TimeoutError:
        rc, out, err = None, "", f"timed out after the ticket's stuck budget ({ticket.stuck_minutes}m)"
        road = "make the command finish within the ticket's stuck budget or correct that budget and retry"
    except ExecutableNotFound as exc:
        rc, out, err = None, "", str(exc)
        road = "install the executable or correct argv/PATH in the child environment and retry"
    if stdout_capture is not None:
        stdout_capture.append(out)
    seconds = (ctx.driver.clock() - started).total_seconds()
    ctx.driver.spool.write(ticket.stem, attempt, name, f"$ {' '.join(argv)}\n[exit {rc}]\n--- stdout\n{out}\n--- stderr\n{err}")
    tail = ctx.driver.redactor.scrub((out + err)[-OUTPUT_TAIL_CHARS:])
    result = CommandResult(argv=list(argv), rc=rc, tail=tail, base_red=False, seconds=seconds)
    findings = [] if rc == 0 else [Finding(message=ctx.driver.redactor.scrub(f"{argv!r} exited {rc}: {tail.strip() or '(no output)'}"), paved_road=road, code=code)]
    return result, GateReport(code=code, verdict="fail" if findings else "pass", findings=findings)


class Evidence(FrozenModel):
    """Everything the mechanical gates judge, gathered once per branch head (the stage layer's job)."""

    stem: NonBlank
    head_sha: NonBlank
    claimed: Literal["ok", "already_satisfied"]
    scope_fence: list[str]
    changed_files: list[str]
    inserted_lines: int
    verification: list[CommandResult]
    run_record: str | None  # the lifted run.md text, None when absent
    core_files: dict[str, bytes | None] = {}
    core_template: bytes = CORE_TEMPLATE
    core_findings: list[Finding] = []
    report_paths: list[str] = []
    report_findings: list[Finding] = []
    is_bug: bool = False
    is_graphics: bool = False
    render: dict = {}
    render_dir: str = ""
    attempt: int = 0
    render_failed: bool = False
    bug_evidence: BugEvidence | None = None
    bug_findings: list[Finding] = []
    meta_findings: list[Finding] = []


def regression_result(stdout: str, rc: int | None) -> Literal["pass", "defect", "error"] | None:
    """Decode the complete common protocol, never a runner's diagnostic or exit vocabulary."""

    def unique(pairs):
        result = dict(pairs)
        if len(result) != len(pairs):
            raise ValueError("duplicate keys")
        return result

    if len(stdout) > OUTPUT_TAIL_CHARS:
        return None
    try:
        result = json.loads(stdout, object_pairs_hook=unique)
    except ValueError, TypeError, RecursionError:
        return None
    if not isinstance(result, dict) or set(result) != {"regression_result"}:
        return None
    value = result["regression_result"]
    if not isinstance(value, str) or value not in {"pass", "defect", "error"}:
        return None
    if (value == "pass" and rc == 0) or (value == "defect" and rc is not None and rc > 0):
        return value
    return "error" if value == "error" else None


def _bug_finding(message: str) -> Finding:
    return Finding(
        code="bug_evidence",
        message=message,
        paved_road="supply durable ticket evidence and carries matching only changed test/fixture files;"
        " provide a carried reproducer checking prerequisites and emitting the regression"
        " result protocol: pass at head, defect at the overlaid base",
    )


async def _gather_bug(ctx: StageContext, ticket: Ticket, evidence: Evidence, *, attempt: int, stage: str) -> tuple[BugEvidence, list[Finding]]:
    worktree = ctx.worktree(ticket.stem)
    base = await ctx.git.merge_base(ctx.repo, MAIN, ticket.stem)
    findings, overlay = [], set()
    for prefix in ticket.carries:
        path = Path(prefix)
        if not prefix or path.is_absolute() or ".." in path.parts or path.as_posix() != prefix.rstrip("/"):
            findings.append(_bug_finding(f"invalid carries prefix {prefix!r}"))
            continue
        matched = [p for p in evidence.changed_files if in_fence(p, [prefix])]
        if not matched:
            findings.append(_bug_finding(f"carries prefix {prefix!r} matches no branch-changed file"))
        for rel in matched:
            if not TEST_FIXTURE_DIRS.intersection(Path(rel).parts[:-1]):
                findings.append(_bug_finding(f"carries path {rel!r} is not a test/fixture file; implementation paths cannot be carried"))
                continue
            tree = await ctx.git._run(ctx.repo, "ls-tree", evidence.head_sha, "--", rel)
            if not tree.startswith(("100644 blob ", "100755 blob ")):
                findings.append(_bug_finding(f"carries path {rel!r} is not a committed regular file"))
                continue
            overlay.add(rel)
    custody = []
    for root in (ctx.repo, worktree):
        directory = root / TICKETS_DIR / ticket.stem / "evidence"
        custody.extend(p.relative_to(root).as_posix() for p in directory.rglob("*") if p.is_file() and not p.is_symlink() and p.resolve().is_relative_to(directory.resolve()))
    record = BugEvidence(
        argv=[ctx.driver.redactor.scrub(arg) for arg in ticket.regression], head_sha=evidence.head_sha, base_sha=base, overlay_paths=sorted(overlay), evidence_paths=sorted(set(custody))
    )
    if not custody:
        findings.append(_bug_finding("durable evidence is missing under the ticket evidence/ directory"))
    if not ticket.regression or not ticket.carries:
        findings.append(_bug_finding("parsed regression command or carries set is missing"))
    if findings:
        return record, findings

    async def execute(root: Path, name: str) -> RegressionRun:
        try:
            rc, out, err = await ctx.exec_.run(list(ticket.regression), cwd=root, env=child_env(ctx.env, ctx.config), timeout=ticket.stuck_minutes * 60.0)
        except (TimeoutError, ExecutableNotFound, OSError) as error:
            rc, out, err = None, "", f"regression execution failed: {error}"
        decoded = regression_result(out, rc)
        ctx.driver.spool.write(ticket.stem, attempt, f"{stage}/regression-{name}.txt", f"$ {' '.join(ticket.regression)}\n[exit {rc}]\n--- stdout\n{out}\n--- stderr\n{err}")
        return RegressionRun(rc=rc, regression_result=decoded, tail=ctx.driver.redactor.scrub(out + err)[-OUTPUT_TAIL_CHARS:])

    head = await execute(worktree, "head")
    base_worktree = await _base_worktree(ctx, ".regression-base", ticket.stem, base)
    try:
        # Restore committed blobs (including executable mode), never dirty checkout copies.
        for rel in overlay:
            if any(p.is_symlink() for p in (base_worktree / rel).parents if p.is_relative_to(base_worktree)):
                return record.model_copy(update={"head": head}), [_bug_finding("base overlay traverses a symlink")]
        await ctx.git.restore(base_worktree, sorted(overlay), source=evidence.head_sha)
        base_run = await execute(base_worktree, "base")
    except GitError as error:
        return record.model_copy(update={"head": head}), [_bug_finding(ctx.driver.redactor.scrub(f"cannot overlay regression inputs: {error}"))]
    finally:
        await ctx.git.worktree_remove(ctx.repo, base_worktree)
    return record.model_copy(update={"head": head, "base": base_run}), findings


def _inserted(diff: str) -> int:
    return sum(line.startswith("+") and not line.startswith("+++") for line in diff.splitlines())


def _names_branch_only_path(argv: Sequence[str], in_branch: Callable[[str], bool], in_base: Callable[[str], bool]) -> bool:
    return any(in_branch(path) and not in_base(path) for token in argv if not token.startswith("-") for path in [token.split("::", 1)[0]])


def render_scratch_dir(state_dir: Path, stem: str, attempt: int) -> Path:
    return state_dir / "scratch" / stem / str(attempt) / "render"


async def gather_evidence(
    ctx: StageContext,
    ticket: Ticket,
    claimed: Literal["ok", "already_satisfied"],
    *,
    attempt: int,
    stage: str = "check",
    safety: Evidence | None = None,
) -> Evidence:
    stem = ticket.stem
    worktree = ctx.worktree(stem)
    outbox = worktree / TICKETS_DIR / stem
    for path in _registered_files(outbox):
        ctx.fs.remove(path)
    results = []
    red: list[tuple[int, list[str]]] = []
    for n, argv in enumerate(ticket.verification, 1):
        result, _ = await run_host_command(ctx, ticket, attempt, list(argv), "verification", f"{stage}/verify-{n:02d}.txt")
        results.append(result)
        if result.rc != 0:
            red.append((n, list(argv)))
    if red:
        base = await ctx.git.merge_base(ctx.repo, MAIN, stem)
        base_worktree = await _base_worktree(ctx, ".base", stem, base)
        try:
            from clutch.daemon import storm_producer_for_config

            box = storm_producer_for_config(ctx.config, fs=ctx.fs, journal=ctx.driver.journal, clock=ctx.driver.clock)
            for n, argv in red:
                baseline, _ = await run_host_command(ctx, ticket, attempt, argv, "verification", f"{stage}/verify-{n:02d}-base.txt", cwd=base_worktree)
                if baseline.rc != 0 and not _names_branch_only_path(argv, lambda p: (worktree / p).exists(), lambda p: (base_worktree / p).exists()):
                    results[n - 1] = results[n - 1].model_copy(update={"base_red": True})
                    summary = f"`{' '.join(argv)}` fails on the merge base {base[:8]} too; fix main, not this ticket"
                    if not any(
                        m.message_class == "failure_report" and m.origin == stem and m.outcome == "base_red" and m.summary.startswith(f"`{' '.join(argv)}` fails on the merge base ")
                        for m in box.messages()
                    ):
                        box.enqueue(message_class="failure_report", origin=stem, stage=stage, outcome="base_red", summary=summary, occurrence_id=arrival_id("base-red", stem, attempt, stage, n))
        finally:
            await ctx.git.worktree_remove(ctx.repo, base_worktree)
    evidence = safety if safety is not None else await gather_safety_evidence(ctx, ticket, claimed)
    reports, findings = [], []
    try:
        _validate_reports(_registered_files(outbox))
        if stage == "check":
            reports = [p.relative_to(worktree).as_posix() for p in _lift_files(ctx, stem, "checks") if p.name in KNOWN_ARTIFACTS and p.name != RUN_FILE]
        elif not evidence.changed_files:
            from clutch.merge import lifted_report_paths

            reports = await lifted_report_paths(ctx, stem, attempt)
    except ArtifactInvalid as error:
        findings.append(
            Finding(
                code="verification",
                path=str(error.path.relative_to(worktree)),
                message=f"invalid registered artifact: {error.error}",
                paved_road="produce a schema-valid registered report through Verification",
            )
        )
    if stage != "check":
        findings.extend(
            Finding(
                code="verification",
                path=f"{TICKETS_DIR}/{stem}/{name}",
                message=f"Verification named {name} but left no report in the outbox",
                paved_road="make the named Verification command exit 0 and write its registered report",
            )
            for name in KNOWN_ARTIFACTS
            if any(f"{TICKETS_DIR}/{stem}/{name}" in arg for argv in ticket.verification for arg in argv) and not (outbox / name).is_file()
        )
    if not evidence.changed_files and claimed == "ok":
        findings.extend(
            Finding(code="verification", path=p, message="uncommitted code in a report-only run", paved_road="commit code on the branch and rerun Check, or remove the edit")
            for p in await dirty_code(ctx, stem)
        )
    bug, bug_findings = await _gather_bug(ctx, ticket, evidence, attempt=attempt, stage=stage) if ticket.frontmatter.kind == "bug" else (None, [])
    render_fields, _ = parse_render(ticket.sections.get("Render", ""), str(ticket_path(stem))) if stage == "check" and evidence.is_graphics else ({}, [])
    render_dir = str(render_scratch_dir(ctx.config.state_dir, stem, attempt)) if render_fields.get("mode") == ["command"] else ""
    return evidence.model_copy(
        update={
            "verification": results,
            "report_paths": reports,
            "report_findings": findings,
            "bug_evidence": bug,
            "bug_findings": bug_findings,
            "render": render_fields,
            "render_dir": render_dir,
            "attempt": attempt if stage == "check" and evidence.is_graphics else 0,
        }
    )


async def gather_safety_evidence(
    ctx: StageContext,
    ticket: Ticket,
    claimed: Literal["ok", "already_satisfied"],
) -> Evidence:
    """Gather the committed metadata once, without verification or base-worktree execution."""
    stem = ticket.stem
    worktree = ctx.worktree(stem)
    run_md = ctx.repo / artifact_path(stem, RUN_FILE)
    changed = await ctx.git.diff_names(ctx.repo, MAIN, stem)
    return Evidence(
        stem=stem,
        head_sha=await ctx.git.rev_parse(ctx.repo, stem),
        claimed=claimed,
        scope_fence=list(ticket.scope_fence),
        changed_files=changed,
        inserted_lines=_inserted(await ctx.git.diff(ctx.repo, MAIN, stem)),
        verification=[],
        is_bug=ticket.frontmatter.kind == "bug",
        is_graphics=ticket.frontmatter.kind == "graphics",
        run_record=run_md.read_text() if run_md.is_file() else None,
        **await committed_core(worktree, ctx.config, ctx.git),
    )


def _report(code: str, findings: list[Finding]) -> GateReport:
    return GateReport(code=code, verdict="fail" if findings else "pass", findings=findings)


def triggered_hosts(ctx, changed_files, *, tier):
    if tier not in {"check", "merge", "integration", "safety"}:
        raise ValueError(f"unknown host check tier: {tier}")
    entries = list(enumerate(ctx.config.review.mechanical, 1))
    if tier == "safety":
        codes = ctx.config.merge.safety_checks
        return [(n, entry) for n, entry in entries if entry.severity == "hard" and entry.code in codes and sum(e.code == entry.code for _, e in entries) == 1]
    if tier == "integration":
        return [(n, entry) for n, entry in entries if entry.trigger == "always" and entry.severity == "hard"]
    return [(n, entry) for n, entry in entries if (tier == "check" or entry.severity == "hard") and (entry.trigger == "always" or any(in_fence(path, entry.trigger) for path in changed_files))]


def _detection_letters(number):
    letters = ""
    while number:
        number, digit = divmod(number - 1, 26)
        letters = chr(ord("a") + digit) + letters
    return letters


def _changed_lines(diff: str) -> dict[str, set[int]]:
    lines: dict[str, set[int]] = {}
    path = None
    new_line = 0
    in_hunk = False
    body = diff.splitlines()
    for i, line in enumerate(body):
        if line.startswith("diff --git "):
            path = None
            new_line = 0
            in_hunk = False
        elif not in_hunk and line.startswith("+++ "):
            name = line[4:]
            if name.startswith('"'):
                name = ast.literal_eval("b" + name).decode("utf-8")
            path = name[2:] if name.startswith("b/") else None
        elif line.startswith("@@ "):
            in_hunk = True
            match = re.match(r"@@ -\d+(?:,\d+)? \+(\d+)", line)
            new_line = int(match[1]) if match else 0
        elif path is not None and new_line:
            if line.startswith("+"):
                lines.setdefault(path, set()).add(new_line)
                new_line += 1
            elif line.startswith("-"):
                if i == 0 or body[i - 1][:1] not in "+-":
                    end = i
                    while end < len(body) and body[end].startswith("-"):
                        end += 1
                    if end == len(body) or not body[end].startswith("+"):
                        lines.setdefault(path, set()).update((max(1, new_line - 1), max(1, new_line)))
            elif line.startswith(" "):
                new_line += 1
    return lines


def flake_covered(report: dict, changed: dict[str, set[int]]) -> bool:
    try:
        files = report["files"]
        if not isinstance(files, dict):
            raise ValueError("invalid files")
        covered = False
        for name, data in files.items():
            lines = data["executed_lines"]
            if not isinstance(name, str) or not isinstance(lines, list) or any(type(line) is not int or line < 1 for line in lines):
                raise ValueError("invalid executed lines")
            covered |= bool(changed.get(name, set()).intersection(lines))
        return covered
    except (KeyError, TypeError) as exc:
        raise ValueError("invalid coverage report") from exc


async def _check_host_results(ctx, ticket, entry, n, attempt, changed_files):
    from clutch.covgate import percentages
    from clutch.daemon import flake_detection, storm_producer_for_config
    from clutch.flake import GreenRerunEvidence, RerunEvidence, release_identity
    from clutch.gates import TestCoverage, TestTiming
    from clutch.testreport import ResultsInvalid, read_results, slow_tests

    root = ctx.worktree(ticket.stem)
    path = root / entry.results
    box = storm_producer_for_config(ctx.config, fs=ctx.fs, journal=ctx.driver.journal, clock=ctx.driver.clock)
    escalations = []
    flake = flake_detection(journal=ctx.driver.journal, box=box, config=ctx.config, escalate=escalations.append)

    async def run(name, selected=None):
        ctx.fs.remove(path)
        argv = entry.argv
        if selected is not None:
            selection_path = path.with_suffix(".select.json")
            ctx.fs.write(selection_path, json.dumps(selected).encode("utf-8"))
            # Serve passes a frozen ConfigSnapshot whose argv is a tuple.
            argv = [*entry.argv, "--clutch-select", str(selection_path)]
        result, report = await run_host_command(ctx, ticket, attempt, argv, entry.code, name)
        try:
            results = read_results(path.read_text())
        except OSError, UnicodeError, ResultsInvalid:
            results = None
        return result, report, results

    def invalid():
        return _report(
            entry.code,
            [
                Finding(
                    code=entry.code,
                    path=entry.results,
                    message=f"Missing or invalid results file: {entry.results}",
                    paved_road=f"make the command write it via -p clutch.testreport --clutch-results {entry.results}",
                )
            ],
        )

    result, report, first = await run(f"check/host-{n:02d}.txt")
    if first is None:
        return invalid() if result.rc == 0 else report
    timing = TestTiming(
        seconds=result.seconds,
        passed=list(first.tests.values()).count("passed"),
        failed=list(first.tests.values()).count("failed"),
        skipped=list(first.tests.values()).count("skipped"),
        slow=slow_tests(first.seconds, entry.slow_test_seconds, entry.slow_test_limit),
    )
    coverage = None
    if entry.coverage is not None:
        try:
            percent, files = percentages(json.loads((root / entry.coverage).read_text()))
            coverage = TestCoverage(percent=percent, files={path: value for path, value in files.items() if path in changed_files})
        except OSError, UnicodeError, ValueError:
            if result.rc == 0:
                return _report(
                    entry.code,
                    [
                        Finding(
                            code=entry.code,
                            path=entry.coverage,
                            message=f"Missing or invalid coverage report: {entry.coverage}",
                            paved_road=f"write the report with --cov-report=json:{entry.coverage}",
                        )
                    ],
                )

    def recorded(report):
        return report.model_copy(update={"timing": timing, "coverage": coverage})

    first = first.tests
    last = first
    if result.rc != 0 and "failed" in first.values():
        selected = [test for test, outcome in first.items() if outcome == "failed"] if entry.coverage is None else None
        result, report, last = await run(f"check/host-{n:02d}-rerun.txt", selected)
        if last is None:
            return invalid()
        last = last.tests
        projection = flake.quarantine()
        findings = []
        flaky = {test for test, outcome in first.items() if outcome == "failed" and last.get(test) == "passed"}
        changed = _changed_lines(await ctx.git.diff(ctx.repo, MAIN, ticket.stem)) if flaky and entry.coverage is not None else {}
        for k, test in enumerate(sorted(flaky), 1):
            edited = test.split("::", 1)[0] in changed_files
            if not edited and entry.coverage is not None:
                try:
                    if entry.flake_coverage_argv is None:
                        raise ValueError("missing flake coverage command")
                    ctx.fs.remove(root / entry.coverage)
                    await run_host_command(ctx, ticket, attempt, entry.flake_coverage_argv + [test], entry.code, f"check/host-{n:02d}-flake-{k}.txt")
                    edited = flake_covered(json.loads((root / entry.coverage).read_text()), changed)
                except OSError, UnicodeError, ValueError, TypeError:
                    return recorded(
                        _report(
                            entry.code,
                            [
                                Finding(
                                    code=entry.code,
                                    path=entry.coverage,
                                    message=f"Missing or invalid flake coverage report: {entry.coverage}",
                                    paved_road=f"configure flake_coverage_argv to write --cov-report=json:{entry.coverage}",
                                )
                            ],
                        )
                    )
            if edited:
                findings.append(Finding(code=entry.code, message=f"{test} is flaky and touches edited code", paved_road="make it deterministic by faking time, IO and ordering"))
            elif test not in projection.tests:
                count = 1 + sum(identity.test_id == test and box_id not in projection.active for box_id, identity in projection.detected.items())
                projection = flake.detect(
                    test_id=test,
                    evidence=RerunEvidence(test, "fail", "pass", True, True, True),
                    summary=f"{test} failed then passed for {ticket.stem}",
                    reason=f"failed then passed on a bare rerun; detection {_detection_letters(count)}",
                    occurrence_id=arrival_id("flake-detection", ticket.stem, attempt, test, n),
                )
                if test not in projection.tests:
                    findings.append(Finding(code=entry.code, message=f"{test}: {escalations[-1]}", paved_road="fix and release existing quarantines before admitting this test"))
        for test, outcome in sorted(last.items()):
            if outcome == "failed" and (test not in projection.tests or test.split("::", 1)[0] in changed_files):
                findings.append(Finding(code=entry.code, message=f"{test} failed on rerun", paved_road="fix the failing test"))
        if result.rc != 0 and "failed" not in last.values():
            findings.extend(report.findings)
        report = _report(entry.code, findings)

    events = ctx.driver.journal.read()
    for identity in list(flake.quarantine().active.values()):
        if {**first, **last}.get(identity.test_id) != "passed":
            continue
        message = box.get(identity.box_id)
        kind, fix = release_identity(message)
        if fix and (kind == "declined" or any(event.type == EventType.STATE_TRANSITION and event.ticket == fix and event.body.get("to") == "merged" for event in events)):
            flake.release(box_id=identity.box_id, evidence=GreenRerunEvidence(identity.test_id, fix, ctx.driver.clock(), "pass", True, True, True))
    return recorded(report)


def decode_render(stdout: str, rc: int | None) -> tuple[str, list[str]] | None:
    def unique(pairs):
        result = dict(pairs)
        if len(result) != len(pairs):
            raise ValueError("duplicate keys")
        return result

    if len(stdout) > OUTPUT_TAIL_CHARS:
        return None
    try:
        result = json.loads(stdout, object_pairs_hook=unique)
    except ValueError, TypeError, RecursionError:
        return None
    if not isinstance(result, dict):
        return None
    if result == {"render_result": "error"}:
        return "error", []
    if set(result) == {"render_result", "artifacts"} and result["render_result"] == "ok" and rc == 0:
        artifacts = result["artifacts"]
        if isinstance(artifacts, list) and all(isinstance(path, str) for path in artifacts):
            return "ok", artifacts
    return None


def artifact_problem(path: str, data: bytes | None) -> str | None:
    if data is None:
        return "artifact is missing"
    if not data:
        return "artifact is empty"
    suffix = Path(path).suffix.lower()
    if suffix == ".png" and not data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "artifact is not a PNG"
    if suffix == ".svg":
        try:
            root = ET.fromstring(data)
        except ET.ParseError, ValueError:
            return "artifact is not an SVG"
        if root.tag not in {"svg", "{http://www.w3.org/2000/svg}svg"}:
            return "artifact is not an SVG"
    if suffix == ".html" and not re.search(rb"<html(?:\s|>)", data, re.IGNORECASE):
        return "artifact is not HTML"
    return None


async def check_render(ctx, ticket, attempt):
    if ticket.frontmatter.kind != "graphics":
        return [], []
    fields, errors = parse_render(ticket.sections.get("Render", ""), str(ticket_path(ticket.stem)))
    if fields.get("mode") != ["command"]:
        return [], []
    road = "correct the Render declaration or renderer output and retry Check"

    def fail(message):
        finding = Finding(code="render", message=message, paved_road=road)
        return [_report("render", [finding])], [finding]

    if errors:
        return fail("invalid Render declaration")
    stdout = []
    result, _ = await run_host_command(ctx, ticket, attempt, fields["command"][0], "render", "check/render.txt", stdout_capture=stdout)
    decoded = decode_render(stdout[0], result.rc)
    if decoded is None:
        return fail("invalid render result protocol or exit status")
    if decoded[0] == "error":
        return fail("renderer reported a missing prerequisite")
    paths = decoded[1]
    if any(not path or Path(path).is_absolute() or ".." in Path(path).parts for path in paths):
        return fail("render artifact paths must be repo-relative without ..")
    declared = fields.get("artifact", [])
    if len(paths) != len(set(paths)) or set(paths) != set(declared):
        return fail("render artifact list does not match the declared artifacts")
    artifacts = []
    for path in paths:
        try:
            data = ctx.fs.read_bytes(ctx.worktree(ticket.stem) / path)
        except OSError:
            data = None
        problem = artifact_problem(path, data)
        if problem:
            return fail(f"{path}: {problem}")
        artifacts.append((path, data))
    for path, data in artifacts:
        ctx.fs.write(render_scratch_dir(ctx.config.state_dir, ticket.stem, attempt) / path, data)
    return [_report("render", [])], []


async def check_hosts(ctx, ticket, changed_files, attempt):
    reports, hard = [], []
    for n, entry in triggered_hosts(ctx, changed_files, tier="check"):
        if entry.results is None:
            _, report = await run_host_command(ctx, ticket, attempt, entry.argv, entry.code, f"check/host-{n:02d}.txt")
        else:
            report = await _check_host_results(ctx, ticket, entry, n, attempt, changed_files)
        if report.verdict == "fail":
            base = await ctx.git.merge_base(ctx.repo, MAIN, ticket.stem)
            base_worktree = await _base_worktree(ctx, ".base", ticket.stem, base)
            try:
                baseline, _ = await run_host_command(ctx, ticket, attempt, entry.argv, entry.code, f"check/host-{n:02d}-base.txt", cwd=base_worktree)
            finally:
                await ctx.git.worktree_remove(ctx.repo, base_worktree)
            if baseline.rc != 0:
                from clutch.daemon import storm_producer_for_config

                box = storm_producer_for_config(ctx.config, fs=ctx.fs, journal=ctx.driver.journal, clock=ctx.driver.clock)
                prefix = ctx.driver.redactor.scrub(f"`{' '.join(entry.argv)}` fails on the merge base ")
                summary = f"{prefix}{base[:8]} too; fix main, not this ticket"
                if not any(m.message_class == "failure_report" and m.origin == ticket.stem and m.outcome == "base_red" and m.summary.startswith(prefix) for m in box.messages()):
                    box.enqueue(
                        message_class="failure_report", origin=ticket.stem, stage="check", outcome="base_red", summary=summary, occurrence_id=arrival_id("base-red", ticket.stem, attempt, "check", n)
                    )
                report = _report(entry.code, [])
            elif entry.severity == "hard":
                hard.extend(report.findings)
        reports.append(report)
    return reports, hard


class ScopeFenceGate:
    """The implement stage's write allowlist: the committed diff within `## Scope fence`.

    The stem's own outbox is exempt except `ticket.md`, which stays read-only to the agent.
    """

    code = "scope_fence"

    def check(self, artifact: Evidence, workspace: Path) -> GateReport:
        outbox = f"{TICKETS_DIR}/{artifact.stem}/"
        outside = [p for p in artifact.changed_files if not in_fence(p, artifact.scope_fence) and not (p.startswith(outbox) and p != outbox + TICKET_FILE)]
        return _report(
            self.code,
            [
                Finding(
                    code=self.code,
                    path=p,
                    message=f"{p} is outside `## Scope fence`",
                    paved_road="revert the edit and commit; if the criteria force it, reply premise_failed naming the file so the fence is widened",
                )
                for p in outside
            ],
        )


class VerificationGate:
    """The ticket's own `## Verification` commands, with base-red failures attributed to main.

    An empty `ok` diff needs current checks-lift report custody.
    """

    code = "verification"

    def check(self, artifact: Evidence, workspace: Path) -> GateReport:
        findings = [
            *artifact.report_findings,
            *[
                Finding(
                    code=self.code, message=f"`{' '.join(r.argv)}` exited {r.rc}: {r.tail.strip() or '(no output)'}", paved_road=f"make `{' '.join(r.argv)}` exit 0 on the branch and commit the fix"
                )
                for r in artifact.verification
                if r.rc != 0 and not r.base_red
            ],
        ]
        empty = not artifact.changed_files
        if empty and artifact.claimed == "ok" and (not artifact.report_paths or any(r.rc != 0 for r in artifact.verification)):
            findings.append(
                Finding(
                    code=self.code,
                    message="the branch carries no committed change",
                    paved_road="commit code on the branch, produce a registered report through"
                    " Verification and leave it uncommitted for the checks lift, or"
                    " reply already_satisfied if every criterion already holds",
                )
            )
        if not empty and artifact.claimed == "already_satisfied":
            findings.append(
                Finding(
                    code=self.code,
                    message=f"already_satisfied was claimed but the branch carries a diff: {', '.join(artifact.changed_files)}",
                    paved_road="reply ok for a branch with changes; already_satisfied commits nothing",
                )
            )
        return _report(self.code, findings)


class RunRecordGate:
    """`run.md` present with the fixed section set and a closed-vocab `## Outcome`."""

    code = "run_record"

    def check(self, artifact: Evidence, workspace: Path) -> GateReport:
        path = artifact_path(artifact.stem, RUN_FILE)
        road = "re-run Implement so the engine writes run.md with every required section"
        if artifact.run_record is None:
            return _report(self.code, [Finding(code=self.code, path=path, message="run.md is missing", paved_road=road)])
        sections: dict[str, list[str]] = {}
        current = None
        for line in artifact.run_record.splitlines():
            if line.startswith("## "):
                current = line[3:].strip()
                sections[current] = []
            elif current is not None:
                sections[current].append(line)
        findings = []
        if tuple(sections) != RUN_RECORD_SECTIONS:
            findings.append(Finding(code=self.code, path=path, message=f"run.md sections are {list(sections)}", paved_road=f"use exactly {list(RUN_RECORD_SECTIONS)}, in order"))
        outcome = "\n".join(sections.get("Outcome", [])).strip()
        if outcome not in OUTCOMES:
            findings.append(Finding(code=self.code, path=path, message=f"`## Outcome` {outcome!r} is not an outcome", paved_road=f"use one of {sorted(OUTCOMES)}"))
        return _report(self.code, findings)


class DiffBudgetGate:
    """A mechanical cap on the reviewable diff, so the review prompt fits its bound."""

    code = "diff_budget"

    def check(self, artifact: Evidence, workspace: Path) -> GateReport:
        inserted = artifact.inserted_lines
        if inserted <= DIFF_BUDGET_INSERTED:
            return _report(self.code, [])
        return _report(
            self.code,
            [
                Finding(
                    code=self.code,
                    message=f"diff is {inserted} inserted lines, over the budget of {DIFF_BUDGET_INSERTED} lines",
                    paved_road="split the ticket into smaller stems, each under the diff budget",
                )
            ],
        )


class MetaDriftGate:
    """Report metadata that needs human review after refresh."""

    code = "meta_drift"

    def check(self, artifact: Evidence, workspace: Path) -> GateReport:
        return _report(self.code, artifact.meta_findings)


class BugEvidenceGate:
    """A new test proves a defect only when its carried reproducer reaches the defect on base."""

    code = "bug_evidence"

    def check(self, artifact: Evidence, workspace: Path) -> GateReport:
        if not artifact.is_bug:
            return _report(self.code, [])
        record = artifact.bug_evidence
        findings = list(artifact.bug_findings)
        if record is None:
            findings.append(_bug_finding("fresh regression evidence is missing"))
        elif not findings:
            if not record.evidence_paths:
                findings.append(_bug_finding("durable ticket evidence is missing"))
            if record.head_sha != artifact.head_sha:
                findings.append(_bug_finding("regression evidence pins a different candidate head"))
            if record.head is None or record.head.rc != 0 or record.head.regression_result != "pass":
                findings.append(_bug_finding("regression head did not complete with exit 0 and pass"))
            if record.base is None or record.base.rc is None or record.base.rc <= 0 or record.base.regression_result != "defect":
                findings.append(_bug_finding("overlaid base did not complete with a positive exit and defect"))
        return GateReport(code=self.code, verdict="fail" if findings else "pass", findings=findings, bug_evidence=record)


class ImageQualityGate:
    """Judge command render artifacts without writing operator previews."""

    code = "image_quality"

    def check(self, artifact: Evidence, workspace: Path) -> GateReport:
        if not artifact.is_graphics or not artifact.render_dir or artifact.render_failed:
            return _report(self.code, [])
        inputs = [workspace / path for path in artifact.render.get("input", [])]
        findings = []
        for path in artifact.render.get("artifact", []):
            for message in images.judge(Path(artifact.render_dir) / path, inputs, embedding=artifact.render.get("presence") == ["embedding"]):
                findings.append(
                    Finding(
                        code=self.code,
                        path=path,
                        message=message,
                        paved_road=message if "clutchwork[images]" in message or "clutchwork[images-embed]" in message else "correct the image and rerun Check",
                    )
                )
        return _report(self.code, findings)


def write_image_previews(fs: FileSystem, evidence: Evidence, workspace: Path) -> None:
    inputs = [workspace / path for path in evidence.render.get("input", [])]
    for path in evidence.render.get("artifact", []):
        candidate = Path(evidence.render_dir) / path
        fs.write(candidate.with_name(candidate.name + ".side-by-side.png"), images.side_by_side([*inputs, candidate]))
        if inputs:
            fs.write(candidate.with_name(candidate.name + ".heatmap.png"), images.heatmap(inputs[0], candidate))


CHECK_GATES: tuple[ScopeFenceGate | VerificationGate | RunRecordGate | DiffBudgetGate | CoreDriftGate | BugEvidenceGate | ImageQualityGate, ...] = (
    ScopeFenceGate(),
    VerificationGate(),
    RunRecordGate(),
    DiffBudgetGate(),
    CoreDriftGate(),
    BugEvidenceGate(),
    ImageQualityGate(),
)


CHECK_ONLY_GATES = (MetaDriftGate(),)


def check_severity(ctx: StageContext, ticket: Ticket) -> dict[str, Severity]:
    """Config severity with the ticket's `gate_bypass` valve applied: a bypassed code is soft for this ticket."""
    severity = dict(ctx.driver.severity)
    for bypass in ticket.frontmatter.gate_bypass:
        severity[bypass.code] = "soft"
    if ticket.frontmatter.source == "box:retro_finding":
        # Admission provenance is required even when the ticket demotes schema checks.
        severity["ticket_schema"] = "hard"
    return severity


async def check_autofix(ctx, ticket, attempt):
    worktree = ctx.worktree(ticket.stem)
    files = [path for path in await ctx.git.diff_names(ctx.repo, MAIN, ticket.stem) if not in_fence(path, [TICKETS_DIR]) and (worktree / path).is_file()]
    selections = [[path for path in files if any(fnmatch.fnmatch(path, pattern) for pattern in entry.files)] for entry in ctx.config.review.autofix]
    selected = {path for paths in selections for path in paths}
    files = [path for path in files if path in selected]
    if not files:
        return [], []
    before = {path: (worktree / path).read_bytes() for path in files}
    reports = []
    for n, (entry, paths) in enumerate(zip(ctx.config.review.autofix, selections, strict=True), 1):
        if not paths:
            continue
        result, report = await run_host_command(ctx, ticket, attempt, [*entry.argv, *paths], entry.code, f"check/autofix-{n:02d}.txt")
        reports.append(report)
        if result.rc != 0:
            await ctx.git.restore(worktree, files, source=ticket.stem)
            return reports, report.findings
    changed = [path for path in files if (worktree / path).read_bytes() != before[path]]
    if changed:
        await ctx.git.commit(worktree, f"clutch({ticket.stem}): autofix", only=changed)
    return reports, []


async def check_meta(ctx, ticket) -> list[Finding]:
    from clutch import metafill
    from clutch.specs import load_spec

    worktree = ctx.worktree(ticket.stem)
    files = [
        path
        for path in await ctx.git.diff_names(ctx.repo, MAIN, ticket.stem)
        if not in_fence(path, [TICKETS_DIR])
        and (worktree / path).name in ctx.fs.entries((worktree / path).parent)
        and any(path.startswith(entry.root.rstrip("/") + "/") for entry in ctx.config.meta.paths)
    ]
    if not files:
        return []
    tracked = await ctx.git.ls_files(worktree)
    sha = await ctx.git.rev_parse(ctx.repo, ticket.stem)
    before = set(meta.check(ctx.config, worktree, ctx.fs, tracked, sha, files))
    filled = []
    if any(reason in {"empty_purpose", "missing", "drifted"} for _, reason in before):
        spec = load_spec((ctx.specs_dir / "meta.md").read_text())
        ask = metafill.make_ask(ctx.driver, spec, worktree, len(ctx.driver.journal.read()))
        filled, _ = await metafill.fill(ctx.config, worktree, ctx.fs, tracked, sha, spec, ask, files)
    changed, malformed = meta.refresh(ctx.config, worktree, ctx.fs, tracked, sha, files)
    changed = sorted(set(filled) | set(changed))
    after = set(meta.check(ctx.config, worktree, ctx.fs, tracked, sha, files))
    if changed:
        await ctx.git.commit(worktree, f"clutch({ticket.stem}): meta", only=changed)
    roads = {
        "malformed": "fix or remove the block so it has the schema and six keys with a valid kind",
        "empty_purpose": "run clutch meta fill {path} or write the one-line purpose",
        "purpose_unverified": "reread the purpose against the new content and rerun clutch meta fill {path} if it is stale",
    }
    findings = []
    for path in files:
        reason = "malformed" if path in malformed else "empty_purpose" if (path, "empty_purpose") in after else None
        if reason:
            findings.append(Finding(code="meta_drift", path=path, message=f"{path}: {reason}", paved_road=roads[reason].format(path=path)))
    return findings


async def check_candidates(ctx, ticket, attempt):
    """Judge each artifact independently and commit only a complete selection."""
    fields, errors = parse_render(ticket.sections.get("Render", ""), str(ticket_path(ticket.stem)))
    if ticket.frontmatter.kind != "graphics" or fields.get("mode") != ["generate"]:
        return []
    if errors:
        return errors
    stem = ticket.stem
    worktree = ctx.worktree(stem)
    artifacts = fields["artifact"]
    changed = await ctx.git.diff_names(ctx.repo, MAIN, stem)
    forbidden = [p for p in changed if p in artifacts or in_fence(p, [".clutch/renders"])]
    if forbidden:
        return [
            Finding(
                code="candidate_paths",
                message=f"Implement changed forbidden paths: {', '.join(forbidden)}",
                paved_road="Implement writes candidates only under .clutch/renders/<stem>/a<i>/ and never an artifact path",
            )
        ]
    if not resolve_visual_baseline(ctx.config, ctx.driver.journal.read(), specs_dir=ctx.specs_dir).binds:
        return [
            Finding(
                code="visual_undecided",
                message="visual_baseline GO is missing or stale",
                paved_road="the ticket stays parked until a GO visual_baseline is recorded for the current review_visual routing and spec major, then retry",
            )
        ]
    inputs = [worktree / p for p in fields.get("input", [])]
    render_dir = render_scratch_dir(ctx.config.state_dir, stem, attempt)
    ticket_text = ctx.fs.read_bytes(ctx.repo / ticket_path(stem)).decode()
    spec = _spec(ctx, "review_visual")
    selected = []
    undecided = []
    for i, artifact in enumerate(artifacts):
        criteria = []
        for line in _criteria(ticket.sections.get("Acceptance criteria", "")):
            match = re.fullmatch(r"visual:\s*([^:]+):\s*(\S.*)", line)
            if match and match.group(1).strip() == artifact:
                criteria.append(match.group(2))
        ids = visual.rubric_ids(criteria, "generate")
        ranked = []
        keys = {}
        for k in range(int(fields.get("candidates", ["3"])[0])):
            relative = Path(f"a{i}") / f"cand-{k}{Path(artifact).suffix}"
            source = worktree / ".clutch" / "renders" / stem / relative
            try:
                data = ctx.fs.read_bytes(source)
            except OSError:
                continue
            candidate = render_dir / relative
            ctx.fs.write(candidate, data)
            if images.judge(candidate, inputs, **({"embedding": True} if fields.get("presence") == ["embedding"] else {})):
                continue
            ctx.fs.write(candidate.with_name(candidate.name + ".side-by-side.png"), images.side_by_side([*inputs, candidate]))
            if inputs:
                ctx.fs.write(candidate.with_name(candidate.name + ".heatmap.png"), images.heatmap(inputs[0], candidate))
            preservation, presence = images.scores(candidate, inputs)
            material = {
                "ticket": ticket_text,
                "generator_prompt": ticket.sections.get("Goal / Why", ""),
                "images": "\n".join(str(worktree / p) for p in fields.get("input", []) + fields.get("reference", [])),
                "candidates": str(candidate),
                "scores": str((preservation, presence)),
                "rubric": "\n".join(ids),
            }

            async def validate_rubric(reply, call_seq):
                try:
                    visual.parse_reply(reply.model_dump_json(), ids)
                except ValueError as error:
                    return _report("visual_rubric", [Finding(code="visual_rubric", message=str(error), paved_road="return exactly the supplied rubric rows")])
                return _report("visual_rubric", [])

            stage = LlmStage(surface="review_visual", emits=visual.Reply, gates=[], review=validate_rubric, render=lambda _, findings: render(spec, material))
            replies = []
            for j in range(ctx.config.graphics.judge_samples):
                scope = f"a{i}c{k}s{j}"
                result = await ctx.driver.run(
                    stage,
                    ticket,
                    ticket=stem,
                    kind=ticket.frontmatter.kind,
                    attempt=attempt,
                    workspace=worktree,
                    tier=ticket.frontmatter.agent_tier,
                    effort=ticket.frontmatter.agent_effort,
                    stuck_budget=ticket.stuck_minutes * 60.0,
                    expected_budget=ticket.expected_minutes * 60.0,
                    scope_fence=(),
                    key_scope=scope,
                )
                if result.outcome != "ok":
                    return result.findings or [Finding(code="visual_undecided", message=f"visual judge failed for {artifact}", paved_road="retry Check with fresh candidates")]
                replies.append(result.artifact)
                if j == 0:
                    keys[k] = llm_key(stem, scoped_seq(scope, journal_run_seq(ctx.driver.journal.read(), stem)), "review_visual", attempt, result.cost.attempts)
            reply = visual.majority(replies)
            ranked.append((k, reply.verdict, sum(row.verdict == "pass" for row in reply.rows), preservation, presence))
        winner, _ = visual.decide(ranked)
        if winner is None:
            undecided.append(artifact)
        else:
            selected.append((artifact, i, winner, keys[winner]))
    if undecided:
        return [Finding(code="visual_undecided", message=f"visual selection undecided: {', '.join(undecided)}", paved_road="retry with fresh candidates")]
    for artifact, i, winner, _ in selected:
        candidate = render_dir / f"a{i}" / f"cand-{winner}{Path(artifact).suffix}"
        ctx.fs.write(worktree / artifact, ctx.fs.read_bytes(candidate))
    body = "\n".join(f"{artifact}: candidate {winner}, evidence {key}" for artifact, _, winner, key in selected)
    await ctx.git.commit(worktree, f"clutch({stem}): select\n\n{body}", only=artifacts)
    return []


async def check(ctx: StageContext, ticket: Ticket, slip: PackingSlip, *, attempt: int) -> StageResult:
    """Invoicing: run the mechanical gates on the branch head, write + lift `checks.json`."""
    with ctx.driver.stage(stem=ticket.stem, attempt=attempt, surface="check") as event:
        result = await _check(ctx, ticket, slip, attempt=attempt)
        event.end(result.outcome)
        return result


async def _check(ctx: StageContext, ticket: Ticket, slip: PackingSlip, *, attempt: int) -> StageResult:
    stem = ticket.stem
    started = ctx.driver.clock()
    prior_wait = ctx.driver.provider_wait(stem, attempt)

    def active_seconds():
        return max(0, (ctx.driver.clock() - started).total_seconds() - (ctx.driver.provider_wait(stem, attempt) - prior_wait))

    outbox = ctx.worktree(stem) / TICKETS_DIR / stem
    autofix_reports, autofix_hard = await check_autofix(ctx, ticket, attempt) if slip.outcome == "ok" and ctx.config.review.autofix else ([], [])
    meta_findings = await check_meta(ctx, ticket) if ctx.config.meta.paths else []
    candidate_findings = await check_candidates(ctx, ticket, attempt)
    if candidate_findings:
        return refused(candidate_findings, Cost(seconds=active_seconds()))
    evidence = await gather_evidence(ctx, ticket, slip.outcome, attempt=attempt)
    render_reports, render_hard = await check_render(ctx, ticket, attempt)
    evidence = evidence.model_copy(update={"render_failed": bool(render_hard), "meta_findings": meta_findings})
    gated = run_gates((*CHECK_GATES, *CHECK_ONLY_GATES), evidence, ctx.worktree(stem), severity=check_severity(ctx, ticket))
    if evidence.is_graphics and evidence.render_dir and not evidence.render_failed and any(r.code == "image_quality" and r.verdict == "pass" for r in gated.reports):
        write_image_previews(ctx.fs, evidence, ctx.worktree(stem))
    host_reports, host_hard = await check_hosts(ctx, ticket, evidence.changed_files, attempt)
    host_reports.extend(render_reports)
    host_hard.extend(render_hard)
    host_hard.extend(autofix_hard)
    required = [name for name in KNOWN_ARTIFACTS if any(f"{TICKETS_DIR}/{stem}/{name}" in arg for argv in ticket.verification for arg in argv)]
    missing = [name for name in required if not (outbox / name).is_file()]
    required_report = (
        _report(
            "verification",
            [
                Finding(
                    code="verification",
                    path=f"{TICKETS_DIR}/{stem}/{name}",
                    message=f"Verification named {name} but left no report in the outbox",
                    paved_road="make the named Verification command exit 0 and write its registered report",
                )
                for name in missing
            ],
        )
        if missing
        else None
    )
    passed = gated.passed and not host_hard and not missing
    invoice = Invoice(
        produced_by_spec_version=CHECK_SPEC_VERSION,
        produced_at_sha=evidence.head_sha,
        stem=stem,
        passed=passed,
        changed_files=evidence.changed_files,
        inserted_lines=evidence.inserted_lines,
        bypassed=sorted({b.code for b in ticket.frontmatter.gate_bypass}),
        reports=[*autofix_reports, *(r for r in gated.reports if ctx.config.meta.paths or r.code != "meta_drift"), *host_reports, *([required_report] if required_report is not None else [])],
        verification=evidence.verification,
    )
    ctx.fs.write(ctx.worktree(stem) / artifact_path(stem, CHECKS_FILE), (invoice.model_dump_json(indent=2) + "\n").encode())
    try:
        await lift_outbox(ctx, stem, "checks", attempt=attempt)
    except ArtifactInvalid as error:
        ctx.fs.remove(error.path)
        ctx.fs.remove(outbox / CHECKS_FILE)
        finding = Finding(
            code="verification",
            path=str(error.path.relative_to(ctx.worktree(stem))),
            message=f"invalid registered artifact: {error.error}",
            paved_road="produce the report through its named Verification command",
        )
        return refused([finding], Cost(seconds=active_seconds()), artifact=invoice.model_copy(update={"passed": False}))
    except GitError as error:
        finding = Finding(code="verification", message=f"checks lift failed: {error}", paved_road="repair the ticket-plane Git failure and rerun Check")
        return refused([finding], Cost(seconds=active_seconds()), artifact=invoice.model_copy(update={"passed": False}))
    cost = Cost(seconds=active_seconds())
    if not passed:
        hard = [f for r in gated.hard_failures for f in r.findings]
        hard.extend(autofix_hard)
        hard.extend(f for r in host_reports for f in r.findings)
        if required_report is not None:
            hard.extend(required_report.findings)
        return refused(hard, cost, artifact=invoice)
    outcome = "already_satisfied" if slip.outcome == "already_satisfied" else "ok"
    return StageResult(outcome=outcome, artifact=invoice, findings=[*gated.findings, *(f for r in host_reports for f in r.findings)], cost=cost)


# --- Review -------------------------------------------------------------------------------------


def review_stage(ctx: StageContext, ticket_text: str, diff: str, prior_review: str) -> tuple[LlmStage, Spec]:
    """clutch/specs/review.md wired UNCHANGED: the same spec and inputs the review baseline measured."""
    spec = _spec(ctx, "review")

    def render_diff(_: object, findings: list[Finding]) -> str:
        inputs = {"ticket": ticket_text, "diff": diff, "prior_review": prior_review, "retry_findings": findings_text(findings)}
        return render(spec, inputs)

    return LlmStage(surface="review", emits=ReviewVerdict, gates=[], render=render_diff), spec


async def review(ctx: StageContext, ticket: Ticket, invoice: Invoice, *, attempt: int) -> StageResult:
    """Inspect: one separate-session review of `git diff main...<stem>`, pinned to the reviewed SHA.

    approve -> ok; snag and rma -> gate_failed (the review surface is a gate); the
    verdict-keyed artifact lands in `review.md` either way.
    """
    stem = ticket.stem
    reviewed = await ctx.git.rev_parse(ctx.repo, stem)
    diff = await ctx.git.diff(ctx.repo, MAIN, stem)
    prior_path = ctx.repo / artifact_path(stem, REVIEW_FILE)
    try:
        prior = read_review(prior_path.read_text()) if prior_path.is_file() else None
    except ValueError:
        prior = None
    prior_review = findings_text(prior.findings) if isinstance(prior, SnagList) else "none"
    stage, spec = review_stage(ctx, (ctx.repo / ticket_path(stem)).read_text(), diff, prior_review)
    try:
        selected = panel_members(ctx.config, ticket.frontmatter.agent_tier, "review", ticket.frontmatter.kind)
    except ProviderSetupError:
        selected = ()
    size = len(selected) or 1
    kwargs = dict(
        ticket=stem,
        kind=ticket.frontmatter.kind,
        attempt=attempt,
        workspace=ctx.worktree(stem),
        tier=ticket.frontmatter.agent_tier,
        effort=ticket.frontmatter.agent_effort,
        stuck_budget=ticket.stuck_minutes * 60.0,
        expected_budget=ticket.expected_minutes * 60.0,
        scope_fence=(),
    )
    try:
        if size == 1:
            result = await ctx.driver.run(stage, invoice, **kwargs)
        else:
            panel = await ctx.driver.run_panel(stage, invoice, size=size, **kwargs)
    except RenderOverBound as e:
        return StageResult(outcome="premise_failed", artifact=None, findings=[e.finding], cost=Cost())
    if size == 1:
        if result.outcome != "ok":
            return result
        verdict = result.artifact
        assert isinstance(verdict, ReviewVerdict)
    else:
        if not panel.members:
            return StageResult(outcome="infra_error", artifact=None, findings=panel.dropped_findings, cost=Cost())
        for member in panel.members:
            if member.outcome != "ok":
                return member
        replies, members, cost = _panel_combine(panel, selected)
        assert all(isinstance(reply, ReviewVerdict) for reply in replies)
        verdict, facts = findings_union(replies, members, panel.dropped)
        ctx.driver.journal.append(EventType.SIGNAL, {"signal": "panel_facts", "attempt": attempt, "surface": "review", **facts.model_dump()}, ticket=stem)
        result = StageResult(outcome="ok", artifact=verdict, findings=[], cost=cost)
    artifact = EMITS_BY_VERDICT[verdict.verdict](
        produced_by_spec_version=_major(spec),
        produced_at_sha=reviewed,
        stem=stem,
        reviewed_sha=reviewed,
        verdict=verdict.verdict,
        summary=verdict.summary,
        findings=list(verdict.findings),
        spec_version=spec.meta.version,
        provider=result.cost.provider,
        model=result.cost.model,
    )
    ctx.fs.write(ctx.worktree(stem) / artifact_path(stem, REVIEW_FILE), render_review(artifact).encode())
    await lift_outbox(ctx, stem, "review", attempt=attempt)
    if verdict.verdict == "approve":
        return _short(result, "ok", [], artifact)
    return _short(result, "gate_failed", list(verdict.findings), artifact)


# --- composition --------------------------------------------------------------------------------


@dataclass(frozen=True)
class StagesRun:
    """Every stage result of one run, in order; the run stops at the first stage not `ok`."""

    attempt: int
    results: dict[StageName, StageResult] = field(default_factory=dict)
    ticket_sha: str | None = None

    @property
    def last(self) -> tuple[StageName, StageResult]:
        return list(self.results.items())[-1]


async def run_stages(ctx: StageContext, ticket: Ticket) -> StagesRun:
    """Implement -> Check -> Review for one ticket, single worker, in the process holding the lock.

    `already_satisfied`, proven by Check's green verification on an empty diff, stops before Review:
    there is no diff to review and the ticket settles as a no-op.
    """
    boundary = ctx.boundary
    dispatched = last_transition(ctx.driver.journal.read(), ticket.stem) or {}
    run = boundary.run or StagesRun(
        attempt=run_seq(ctx.driver.journal.read(), ticket.stem),
        ticket_sha=(dispatched.get("ticket_sha") if dispatched.get("to") == "running" else None) or await ctx.git.rev_parse(ctx.repo, f"{MAIN}:{ticket_path(ticket.stem)}"),
    )
    boundary.ticket, boundary.next_stage = ticket, None
    for stage in ("implement", "check", "review"):
        if stage in run.results:
            if run.results[stage].outcome != "ok":
                return run
            continue
        if boundary.select is not None and not boundary.select(ticket, stage):
            boundary.run, boundary.next_stage = run, stage
            return run
        if findings := await ticket_change_findings(ctx, ticket.stem, expected=run.ticket_sha):
            run.results[stage] = refused(findings, Cost())
            return run
        if stage == "implement":
            operation = implement(ctx, ticket, attempt=run.attempt)
        elif stage == "check":
            slip = run.results["implement"].artifact
            assert isinstance(slip, PackingSlip)
            operation = check(ctx, ticket, slip, attempt=run.attempt)
        else:
            invoice = run.results["check"].artifact
            assert isinstance(invoice, Invoice)
            operation = review(ctx, ticket, invoice, attempt=run.attempt)
        if boundary.select is None:
            result = await operation
        else:
            boundary.active = asyncio.create_task(operation)
            try:
                result = await asyncio.shield(boundary.active)
            except asyncio.CancelledError:
                await ctx.abort_current()
                raise
            finally:
                boundary.active = None
        run.results[stage] = result
        if result.outcome != "ok":
            break
    return run
