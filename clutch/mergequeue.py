"""Serial merge admission for serve; run and drain merge inline through merge.merge."""

import asyncio
import json
import re
from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING, Literal
from uuid import uuid4

if TYPE_CHECKING:
    from clutch.daemon import PauseConsumer

from pydantic import BaseModel, ConfigDict

from clutch import merge, stages
from clutch.artifacts import Cost, Finding, StageResult, refused
from clutch.drain import authored_at, sort_key
from clutch.driver import LlmStage
from clutch.effects import Effects
from clutch.gates import GateReport, run_gates
from clutch.git import GitError, RebaseRefused
from clutch.journal import Event, EventType
from clutch.specs import RenderOverBound, render
from clutch.stages import CommandResult, Evidence, StageContext
from clutch.tickets import REVIEW_FILE, TICKETS_DIR, Ticket, artifact_path, in_fence, ticket_path, validate_ticket

CONFLICT_FACTS = "merge_conflict_facts"
RED_STREAK = "merge_red_streak"
TREE_MISMATCH = "merge_tree_mismatch"
RED_STREAK_LIMIT = 3
MERGE_REGATE = "merge-regate"
MODEL_MAX_FILES = 3
MODEL_MAX_MARKER_LINES = 60
CONFLICT_MARKER = re.compile(r"^(?:<<<<<<<|=======|>>>>>>>|\|\|\|\|\|\|\|)(?: |$)", re.MULTILINE)


def model_eligible(files: dict[str, tuple[str | None, str | None, str | None]], marked: dict[str, str], inventory: Sequence[str], shared: Sequence[str], renamed: Sequence[str] = ()) -> bool:
    """Bounds apply to the whole admission; shared paths waive only the safety exclusion."""
    return (
        0 < len(files) <= MODEL_MAX_FILES
        and sum(len(CONFLICT_MARKER.findall(text)) for text in marked.values()) <= MODEL_MAX_MARKER_LINES
        and not set(files).intersection(renamed)
        and all(all(text is not None and "\0" not in text for text in contents) for contents in files.values())
        and all(not in_fence(path, inventory) or in_fence(path, shared) for path in files)
    )


class ResolveReply(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", frozen=True)

    verdict: Literal["resolved", "decline"]
    reason: str
    files: dict[str, str]


def regate_receipts(events) -> dict[str, dict]:
    receipts = {}
    road = "restore consistent merge-regate evidence and retained reviewed artifacts before restarting"
    fields = {"stem", "attempt", "reviewed_sha", "candidate_base_sha", "candidate_sha", "checked_tree", "review_provider", "review_model", "admission", "reason"}
    for event in events:
        if event.type != EventType.EFFECT_COMPLETION or not (event.key or "").startswith(MERGE_REGATE + "/"):
            continue
        value = event.body.get("result")
        if (
            not isinstance(value, dict)
            or set(value) != fields
            or type(value.get("attempt")) is not int
            or value["attempt"] < 0
            or not isinstance(value.get("stem"), str)
            or event.ticket != value["stem"]
            or any(not isinstance(value[k], str) or not re.fullmatch(r"[0-9a-f]{40}", value[k]) for k in ("reviewed_sha", "candidate_base_sha", "candidate_sha", "checked_tree"))
            or any(value[k] is not None and (not isinstance(value[k], str) or not value[k].strip()) for k in ("review_provider", "review_model"))
            or value["admission"] not in ("READY", "HELD")
            or value["reason"] not in ("bootstrap", "foreground", "confirmed", "go_covered", "go_absent", "go_revoked", "review_off_baseline")
            or (value["admission"] == "HELD") != (value["reason"] in ("go_absent", "go_revoked", "review_off_baseline"))
            or event.key != f"{MERGE_REGATE}/{value['stem']}/{value['attempt']}/{value['candidate_base_sha']}/{value['candidate_sha']}"
            or event.key in receipts
            and receipts[event.key] != value
        ):
            raise ValueError(road)
        receipts[event.key] = value
    return receipts


class TreeMismatch(RuntimeError):
    """Main has moved, but differs from the checked tree: pause without retiring the branch."""


class MergeQueue:
    def __init__(self, ctx: StageContext, *, escalate: Callable[[Event], None], control: "PauseConsumer | None" = None) -> None:
        self.ctx = ctx
        self.escalate = escalate
        self.pending: dict[str, tuple[Ticket, int]] = {}
        self.active: str | None = None
        self.control = control
        self.hold_id = control.admission if control is not None and control.admission not in control.projection.released_hold_ids else None
        self.paused = self.hold_id is not None
        self.red_stems: list[str] = []
        self._slot = asyncio.Lock()
        self.deliveries: list[tuple[Ticket, int, object]] = []
        self.contexts: dict[str, StageContext] = {}

    def offer(self, ticket: Ticket, *, attempt: int, ctx: StageContext | None = None) -> None:
        self.pending[ticket.stem] = (ticket, attempt)
        self.contexts[ticket.stem] = ctx if ctx is not None else self.ctx

    def _release(self) -> None:
        if self.paused and self.control is not None and self.hold_id in self.control.projection.released_hold_ids:
            self.paused = False
            self.red_stems.clear()
            self.hold_id = None

    def _hold(self, stem: str, body: dict) -> None:
        hold_id = uuid4().hex
        event = self.ctx.driver.journal.append(EventType.SIGNAL, {**body, "hold_id": hold_id}, ticket=stem, key=None)
        self.paused, self.hold_id = True, hold_id
        if self.control is not None:
            self.control.hold(hold_id)
        self.escalate(event)

    async def process(self) -> list[StageResult]:
        results = []
        self.deliveries = []
        async with self._slot:
            while True:
                self._release()
                if not self.pending or self.paused:
                    break
                ages = authored_at(self.ctx.driver.journal.read())
                ticket, attempt = min(self.pending.values(), key=lambda row: sort_key(row[0], ages))
                del self.pending[ticket.stem]
                self.active = ticket.stem
                try:
                    self.ctx = self.contexts.get(ticket.stem, self.ctx)
                    result = await self._admit(ticket, attempt)
                    results.append(result)
                    self.deliveries.append((ticket, attempt, result))
                finally:
                    self.active = None
        return results

    async def retained_ticket(self, stem, receipt):
        ctx = self.ctx
        road = "restore the retained committed ticket, reviewed evidence and candidate; then restart serve"
        try:
            lifts = ctx.driver.effects.recorded(f"ticket-plane/{stem}/{receipt['attempt']}/review")
            source = lifts[-1]["commit"] if lifts else "main"
            text = await ctx.git._run(ctx.repo, "show", f"{source}:{ticket_path(stem)}")
            ticket = validate_ticket(stem, text, ctx.repo)
            review = stages.read_review(await ctx.git._run(ctx.repo, "show", f"main:{artifact_path(stem, REVIEW_FILE)}"))
            if (
                not isinstance(review, stages.ApprovedInvoice)
                or review.stem != stem
                or review.reviewed_sha != receipt["reviewed_sha"]
                or not ctx.worktree(stem).is_dir()
                or await stages.dirty_code(ctx, stem)
                or await ctx.git.rev_parse(ctx.worktree(stem), "HEAD") != await ctx.git.rev_parse(ctx.repo, stem)
            ):
                raise ValueError(road)
            if lifts:
                path = artifact_path(stem, REVIEW_FILE)
                if await ctx.git.rev_parse(ctx.repo, f"main:{path}") != await ctx.git.rev_parse(ctx.repo, f"{source}:{path}"):
                    raise ValueError(road)
            if any(receipt[k] is not None for k in ("review_provider", "review_model")):
                if await stages.served_review(ctx, stem, receipt["attempt"], receipt["reviewed_sha"]) != (receipt["review_provider"], receipt["review_model"]):
                    raise ValueError(road)
            return ticket
        except Exception as exc:
            raise ValueError(f"retained admission {stem} is unavailable: {exc}; {road}") from exc

    async def _finish(self, ticket, attempt, reviewed, checked_tree, started, findings=()):
        completed = bool(self.ctx.driver.effects.recorded(f"merge/{ticket.stem}/{attempt}"))
        admission = await merge.write_squash(self.ctx, ticket, reviewed, attempt=attempt)
        # Recovery proves the completed squash; later ticket commits may already have moved main.
        source = admission.commit if completed and admission.commit is not None else "main"
        main_tree = await self.ctx.git.rev_parse(self.ctx.repo, source + "^{tree}")
        if main_tree != checked_tree:
            self._hold(ticket.stem, {"kind": TREE_MISMATCH, "checked_tree": checked_tree, "main_tree": main_tree})
            raise TreeMismatch(f"{ticket.stem}: checked tree {checked_tree} differs from main tree {main_tree}")
        await merge.retire(self.ctx, ticket.stem)
        return StageResult(outcome="ok", artifact=admission, findings=list(findings), cost=Cost(seconds=(self.ctx.driver.clock() - started).total_seconds()))

    def _signal(self, stem: str, body: dict, *, escalate: bool = False) -> None:
        event = self.ctx.driver.journal.append(EventType.SIGNAL, body, ticket=stem, key=None)
        if escalate:
            self.escalate(event)

    def _facts(self, stem: str, conflicts: set[str], strategies: set[str], *, rerun: bool = False, model: bool = False, red: Sequence[str] = ()) -> None:
        self._signal(
            stem,
            {
                "kind": CONFLICT_FACTS,
                "conflicted_paths": sorted(conflicts),
                "resolving_rung": "rerun" if rerun else "model" if model else "mechanical" if strategies else "none",
                "strategy_paths": sorted(strategies),
                "integration_red_paths": sorted(set(red)),
            },
        )

    def _finding(self, message: str, road: str, *, path: str | None = None, code: str = "post_rebase_regate") -> Finding:
        return Finding(code=code, path=path, message=self.ctx.driver.redactor.scrub(message), paved_road=road)

    async def _command(self, ticket: Ticket, attempt: int, argv: list[str], code: str, name: str) -> tuple[CommandResult, GateReport]:
        return await stages.run_host_command(self.ctx, ticket, attempt, argv, code, name)

    async def host_checks(self, ticket: Ticket, *, attempt: int, safety: bool) -> tuple[list[CommandResult], list[GateReport]]:
        reports = []
        tier = "safety" if safety else "integration"
        if safety:
            for code in self.ctx.config.merge.safety_checks:
                matches = [entry for entry in self.ctx.config.review.mechanical if entry.code == code]
                if len(matches) != 1 or matches[0].severity != "hard":
                    finding = self._finding(
                        f"merge.safety_checks designation {code!r} does not resolve to exactly one hard entry",
                        "declare exactly one hard review.mechanical entry for this code, or remove it from merge.safety_checks",
                    )
                    reports.append(GateReport(code=finding.code, verdict="fail", findings=[finding]))
            if reports:
                return [], reports
        entries = stages.triggered_hosts(self.ctx, [], tier=tier)
        results = []
        for n, entry in entries:
            result, report = await self._command(ticket, attempt, entry.argv, entry.code, f"merge-{tier}/host-{n:02d}.txt")
            results.append(result)
            reports.append(report)
        return results, reports

    def _strategy(self, path: str, ticket: Ticket):
        matches = [s for s in self.ctx.config.merge.strategies if in_fence(path, s.paths)]
        road = "declare exactly one strategy for this path; regenerate paths must be outside the ticket fence"
        if len(matches) != 1:
            return None, self._finding(f"{path} has {len(matches)} matching strategies", road, path=path)
        strategy = matches[0]
        if strategy.strategy == "regenerate" and in_fence(path, ticket.scope_fence):
            return None, self._finding(f"{path} is owned by both regenerate and the ticket fence", road, path=path)
        return strategy, None

    def _scoped(self, evidence: Evidence, ticket: Ticket) -> tuple[Evidence, list[Finding]]:
        exempt, findings = [], []
        for path in evidence.changed_files:
            if any(in_fence(path, s.paths) for s in self.ctx.config.merge.strategies):
                strategy, finding = self._strategy(path, ticket)
                if finding:
                    findings.append(finding)
                elif strategy:
                    exempt.append(path)
        return evidence.model_copy(update={"scope_fence": [*evidence.scope_fence, *exempt]}), findings

    async def _resolve(self, ticket: Ticket, attempt: int, paths: list[str], hits: set[str]) -> list[Finding]:
        worktree = self.ctx.worktree(ticket.stem)
        for path in paths:
            strategy, finding = self._strategy(path, ticket)
            if finding:
                return [finding]
            try:
                if strategy.strategy == "union":
                    base, ours, theirs = [await self.ctx.git._run(worktree, "show", f":{n}:{path}") for n in (1, 2, 3)]
                    if "\0" in base + ours + theirs or not ours.startswith(base) or not theirs.startswith(base):
                        return [self._finding(f"{path} is not an append-only union", "resolve the conflicting edits through Rework and obtain a new approval", path=path)]
                    text = ours + (theirs[len(base) :] if ours != theirs else "")
                    self.ctx.fs.write(worktree / path, text.encode())
                else:
                    await self.ctx.git._run(worktree, "checkout", "--ours", "--", path)
                    _, report = await self._command(ticket, attempt, strategy.argv, "post_rebase_regate", f"merge-resolution/generator-{len(hits) + 1:02d}.txt")
                    if report.verdict == "fail":
                        return report.findings
                await self.ctx.git.add(worktree, [path])
                hits.add(path)
            except GitError as exc:
                return [self._finding(f"cannot resolve {path}: {exc}", "resolve the conflict through Rework and obtain a new approval", path=path)]
        return []

    async def _model_resolve(self, ticket, attempt, paths, files, marked, renamed, reviewed, base):
        ctx = self.ctx
        worktree = ctx.worktree(ticket.stem)
        road = "resolve the conflict through Rework and obtain a new approval"
        if not model_eligible(files, marked, ctx.config.engine_plane_safety_inventory, ctx.config.scheduler.parallel.shared_paths, renamed):
            return None
        try:
            subjects = await ctx.git._run(ctx.repo, "log", "--format=%s", f"{base}..main", "--", *sorted(files))
            others = []
            for stem in dict.fromkeys(re.findall(r"^clutch\(([a-z0-9][a-z0-9-]*)\):", subjects, re.MULTILINE)):
                text = await ctx.git._run(ctx.repo, "show", f"main:{ticket_path(stem)}")
                # Read only the two intent sections, not instructions or unrelated ticket metadata.
                sections = dict(re.findall(r"(?ms)^## ([^\n]+)\n(.*?)(?=^## |\Z)", text))
                others.append({"stem": stem, "goal": sections.get("Goal / Why", ""), "scope": sections.get("Scope in / Scope out", "").split("Scope out:", 1)[0]})
            spec = stages._spec(ctx, "resolve")
            inputs = {
                "ticket": json.dumps({"goal": ticket.sections["Goal / Why"], "scope": ticket.sections["Scope in / Scope out"].split("Scope out:", 1)[0]}),
                "other_tickets": json.dumps(others),
                "conflicts": json.dumps({path: dict(zip(("base", "ours", "theirs"), files[path], strict=True)) for path in paths}),
                "retry_findings": "none",
            }
            stage = LlmStage(surface="resolve", emits=ResolveReply, gates=[], render=lambda _, findings: render(spec, {**inputs, "retry_findings": stages.findings_text(findings)}))
            kwargs = dict(
                ticket=ticket.stem,
                attempt=attempt,
                workspace=worktree,
                stuck_budget=ticket.stuck_minutes * 60.0,
                expected_budget=ticket.expected_minutes * 60.0,
                scope_fence=(),
                key_scope=f"resolve{len(files)}{await ctx.git.rev_parse(worktree, 'REBASE_HEAD')}",
            )
            result = await ctx.driver.run(stage, None, tier=spec.meta.tier, effort=spec.meta.effort, **kwargs)
            reply = result.artifact
            if result.outcome != "ok" or not isinstance(reply, ResolveReply):
                return result.findings or [self._finding("model resolution failed", road)]
            if reply.verdict == "decline":
                return [self._finding(f"model declined: {reply.reason}", road, path=paths[0])]
            if set(reply.files) != set(paths) or any("\0" in text or CONFLICT_MARKER.search(text) for text in reply.files.values()):
                return [self._finding("model resolution has incorrect paths, binary text or conflict markers", road)]
            # Validate the entire reply before writing or staging any file.
            for path, text in reply.files.items():
                ctx.fs.write(worktree / path, text.encode())
            await ctx.git.add(worktree, paths)
            delta = await ctx.git._run(worktree, "diff", "--cached", reviewed, "--", *paths)
            review, review_spec = stages.review_stage(ctx, (await ctx.git._run(ctx.repo, "show", f"main:{ticket_path(ticket.stem)}")), delta, "none")
            checked = await ctx.driver.run(review, None, tier=review_spec.meta.tier, effort=review_spec.meta.effort, **kwargs)
            if checked.outcome != "ok" or not isinstance(checked.artifact, stages.ReviewVerdict) or checked.artifact.verdict != "approve":
                return checked.findings or [self._finding("model resolution review did not approve", road)]
            return []
        except (GitError, RenderOverBound, UnicodeError) as exc:
            return [self._finding(f"model resolution unavailable: {exc}", road)]

    async def _admit(
        self,
        ticket: Ticket,
        attempt: int,
        *,
        conflict_ladder: bool = True,
        safety_tier: bool = True,
        receipt: bool = True,
        tree_check: bool = True,
        red_streak: bool = True,
        conflict_facts: bool = True,
        inline_hosts: bool = False,
        gather_stage: str = "merge-integration",
        strategy_scope: bool = True,
        receipt_lookup: bool = True,
    ) -> StageResult:
        ctx, stem = self.ctx, ticket.stem
        worktree = ctx.worktree(stem)
        started = ctx.driver.clock()
        conflicts, hits = set(), set()
        rebasing = False
        model = False
        files, marked, renamed = {}, {}, set()

        def elapsed() -> Cost:
            return Cost(seconds=(ctx.driver.clock() - started).total_seconds())

        def facts(*args, **kwargs):
            if conflict_facts:
                self._facts(*args, model=model, **kwargs)

        if findings := await stages.ticket_change_findings(ctx, stem):
            return refused(findings, elapsed() if conflict_ladder else Cost())

        try:
            receipts = [r for r in regate_receipts(ctx.driver.journal.read()).values() if r["stem"] == stem and r["attempt"] == attempt and r["admission"] == "HELD"] if receipt_lookup else []
            reviewed = receipts[-1]["reviewed_sha"] if receipts else await ctx.git.rev_parse(ctx.repo, stem)
            unchanged = await merge.main_code_unchanged(ctx, reviewed)
            candidate_base = await ctx.git.rev_parse(ctx.repo, "main") if receipt else None
            await ctx.git.restore(worktree, [TICKETS_DIR], source=stem)
            rebasing = True
            step = ctx.git.rebase_stop_at_conflict(worktree, stages.MAIN) if conflict_ladder else ctx.git.rebase(worktree, stages.MAIN)
            while True:
                try:
                    await step
                    rebasing = False
                    break
                except RebaseRefused as exc:
                    rebasing = False
                    facts(stem, conflicts, hits)
                    message = f"rebase onto main refused: {exc.err.strip()}"
                    road = f"re-run `engine run {stem}` so Implement re-branches from current main"
                    finding = self._finding(message, road) if conflict_ladder else Finding(code="post_rebase_regate", message=message, paved_road=road)
                    return refused([finding], elapsed())
                except GitError:
                    paths = await ctx.git.conflicted_paths(worktree)
                    conflicts.update(paths)
                    # Missing index stages reject modify/delete and rename conflicts.
                    for path in paths:
                        contents = []
                        for n in (1, 2, 3):
                            try:
                                contents.append(await ctx.git._run(worktree, "show", f":{n}:{path}"))
                            except GitError:
                                contents.append(None)
                        files[path] = tuple(contents)
                        try:
                            marked[path] = marked.get(path, "") + "\n" + ctx.fs.read_bytes(worktree / path).decode("utf-8", errors="replace")
                        except FileNotFoundError:
                            marked[path] = ""
                    base = await ctx.git.merge_base(ctx.repo, reviewed, "main")
                    for ref in (reviewed, "main"):
                        changes = await ctx.git._run(ctx.repo, "diff", "--name-status", "-M", base, ref)
                        for line in changes.splitlines():
                            if line.startswith("R"):
                                renamed.update(line.split("\t")[1:])
                    findings = await self._resolve(ticket, attempt, paths, hits)
                    if findings and conflict_ladder:
                        remaining = await ctx.git.conflicted_paths(worktree)
                        resolution = await self._model_resolve(ticket, attempt, remaining, files, marked, renamed, reviewed, base)
                        if resolution is not None:
                            findings = findings + resolution if resolution else []
                            model = model or not findings
                    if findings:
                        await ctx.git._call(worktree, "rebase", "--abort")
                        rebasing = False
                        facts(stem, conflicts, hits, rerun=True)
                        return refused(
                            [self._finding("merge conflict requires fresh implementation", "re-implement from current main", path=path, code="merge_conflict_rerun") for path in sorted(conflicts)]
                            + findings,
                            elapsed(),
                        )
                    step = ctx.git.rebase_continue(worktree)

            evidence = await stages.gather_safety_evidence(ctx, ticket, "ok")
            skip = unchanged and bool(evidence.changed_files) and not receipts and not model
            candidate = merge.read_candidate(ctx, ticket, reviewed, evidence.changed_files)
            severity = stages.check_severity(ctx, ticket)
            scoped, strategy_findings = self._scoped(evidence, ticket) if strategy_scope else (evidence, [])
            safety = []
            if safety_tier:
                safety.append(run_gates((g for g in stages.CHECK_GATES if g.code in {"scope_fence", "run_record"}), scoped, worktree, severity=severity))
            if safety_tier or skip:
                safety.append(run_gates(merge.MERGE_GATES, candidate, ctx.repo, severity=severity))
            _, host = ([], []) if skip or not safety_tier else await self.host_checks(ticket, attempt=attempt, safety=True)
            hard = strategy_findings + [f for g in safety for r in g.hard_failures for f in r.findings]
            hard += [f for r in host if r.verdict == "fail" for f in r.findings]
            if hard:
                facts(stem, conflicts, hits)
                return refused(hard, elapsed())

            integration = []
            if not skip:
                evidence = await stages.gather_evidence(ctx, ticket, "ok", attempt=attempt, stage=gather_stage, safety=evidence)
                scoped, strategy_findings = self._scoped(evidence, ticket) if strategy_scope else (evidence, [])
                candidate = merge.read_candidate(ctx, ticket, reviewed, evidence.changed_files)
                integration = [run_gates(stages.CHECK_GATES, scoped, worktree, severity=severity), run_gates(merge.MERGE_GATES, candidate, ctx.repo, severity=severity)]
                if inline_hosts:
                    host = []
                    for n, entry in stages.triggered_hosts(ctx, evidence.changed_files, tier="merge"):
                        _, report = await self._command(ticket, attempt, entry.argv, entry.code, f"merge/host-{n:02d}.txt")
                        host.append(report)
                else:
                    _, host = await self.host_checks(ticket, attempt=attempt, safety=False)
                hard = strategy_findings + [f for g in integration for r in g.hard_failures for f in r.findings]
                hard += [f for r in host if inline_hosts or r.verdict == "fail" for f in r.findings]
                facts(stem, conflicts, hits, red=evidence.changed_files if hard else [])
                if hard:
                    if red_streak and stem not in self.red_stems:
                        self.red_stems.append(stem)
                    if red_streak and len(self.red_stems) == RED_STREAK_LIMIT:
                        self._hold(stem, {"kind": RED_STREAK, "stems": list(self.red_stems), "limit": RED_STREAK_LIMIT})
                    return refused(hard, elapsed())
                if red_streak:
                    self.red_stems.clear()
            else:
                facts(stem, conflicts, hits)
            if not receipt and not tree_check:
                if findings := await merge.dirty_overlap(ctx, stem):
                    return refused(findings, elapsed())
                admission = await merge.write_squash(ctx, ticket, reviewed, attempt=attempt)
                await merge.retire(ctx, stem)
                return StageResult(outcome="ok", artifact=admission, findings=[f for g in integration + safety for f in g.findings], cost=Cost(seconds=(ctx.driver.clock() - started).total_seconds()))
            checked_tree = await ctx.git.rev_parse(worktree, "HEAD^{tree}")
            candidate_sha = await ctx.git.rev_parse(worktree, "HEAD")
            key = f"{MERGE_REGATE}/{stem}/{attempt}/{candidate_base}/{candidate_sha}"

            served = await stages.served_review(ctx, stem, attempt, reviewed)

            async def receipt_action():
                return dict(
                    stem=stem,
                    attempt=attempt,
                    reviewed_sha=reviewed,
                    candidate_base_sha=candidate_base,
                    candidate_sha=candidate_sha,
                    checked_tree=checked_tree,
                    review_provider=served[0],
                    review_model=served[1],
                    admission="READY",
                    reason="bootstrap",
                )

            if findings := await merge.dirty_overlap(ctx, stem):
                return refused(findings, elapsed())
            await Effects(ctx.driver.journal).run(receipt_action, key=key, ticket=stem)
            return await self._finish(ticket, attempt, reviewed, checked_tree, started, [f for g in safety + integration for f in g.findings])
        finally:
            if rebasing:
                # Shield cleanup from the cancellation that triggered unwinding.
                abort = asyncio.create_task(ctx.git._call(worktree, "rebase", "--abort"))
                try:
                    await asyncio.shield(abort)
                except asyncio.CancelledError:
                    await abort
                    raise
