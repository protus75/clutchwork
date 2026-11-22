"""The Suggestion Box Author stage."""

import json
import re
import shutil
from dataclasses import dataclass
from pathlib import Path

import duckdb
import yaml
from pydantic import BaseModel, ConfigDict, field_validator

from clutch import calibration, context, index
from clutch.artifacts import Finding, NonBlank
from clutch.baseline import resolve_baseline
from clutch.box import BOX_DIR, Box, BoxError, DecisionRecord, Message, Resolution, record_path, render_record
from clutch.driver import Driver, LlmStage, unwrap_fence
from clutch.gates import GateReport
from clutch.git import GitError, NothingToCommit, blob_sha
from clutch.inbox import CAPS, bounded, report_data
from clutch.journal import EventType
from clutch.policy import policy_row, start_state
from clutch.providers import child_env
from clutch.requisition import FIRST_REVIEW, RequisitionVerdict, render_prior_review, review_with_identity
from clutch.runner import SPECS_DIR, Checkout
from clutch.specs import Spec, load_spec, render
from clutch.stages import findings_text
from clutch.status import SETTLED, last_states
from clutch.tickets import KINDS, TicketInvalid, split_frontmatter, stamp, stem_findings, template, ticket_path, validate_ticket

AUTHOR_STUCK_S = 900.0
PLAN_WHOLE_CHARS = 40_000


def context_block(state_dir: Path, text: str, stem: str, *, connect=duckdb.connect) -> str:
    try:
        if not text.strip():
            return "none"
        path = state_dir / "index.duckdb"
        if not path.exists():
            return "unavailable: no_index (run clutch index build)"
        conn = connect(str(path), read_only=True)
        try:
            _, sections = context.suggest(conn, stem, [], [], text)
            return "\n".join(f"- {selector}  # {reason}" for selector, reason in sections) or "none"
        finally:
            conn.close()
    except Exception:
        return "unavailable: index_unreadable"


async def neighbors_block(checkout, text, exclude_id, *, neighbors=index.neighbors, exclude_refs: tuple[str, ...] = ()) -> str:
    try:
        if not isinstance(text, str) or not text.strip():
            return "none"
        result = await neighbors(
            checkout.config,
            checkout.repo,
            text.strip()[:8000],
            fs=checkout.fs,
            exec_=checkout.exec_,
            env=child_env(checkout.env, checkout.config, serving=None),
            creator=index.default_creator,
            limit=5,
            exclude=(exclude_id, f"tickets/decisions/declined-{exclude_id}.md", f"tickets/decisions/tombstone-{exclude_id}.md", *exclude_refs),
        )
        if result.outcome == "no_match":
            return "none"
        if result.outcome == "no_index":
            return "unavailable: no_index (run clutch index build)"
        if result.outcome != "found":
            return f"unavailable: {result.outcome}"

        def bounded(value, limit):
            value = " ".join(value.split())
            return value if len(value) <= limit else value[: limit - 3] + "..."

        return "\n".join([f"mode: {result.mode}"] + [f"- {hit.kind} {bounded(hit.ref, 100)} (score {hit.score:.3f}): {bounded(hit.text, 200)}" for hit in result.hits[:5]])
    except Exception:
        return "unavailable: index_unreadable"


def plan_excerpt(text: str) -> str:
    if len(text) < PLAN_WHOLE_CHARS:
        return text
    sections = []
    current = None
    fenced = False
    for line in text.splitlines(keepends=True):
        if line.startswith("```"):
            fenced = not fenced
        elif not fenced and line.startswith("## "):
            if current is not None:
                sections.append("".join(current).rstrip("\n"))
            current = [line] if line.rstrip("\r\n") in {"## Target design", "## Where each piece lives"} else None
            continue
        if current is not None:
            current.append(line)
    if current is not None:
        sections.append("".join(current).rstrip("\n"))
    return "\n\n".join(sections) if sections else "Plan exceeds the 40,000-character bound and has neither Target design nor Where each piece lives; read the plan file at the row's plan path."


class AuthorReply(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    stem: NonBlank
    ticket: str

    @field_validator("ticket")
    @classmethod
    def ticket_nonblank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("ticket must be nonblank")
        return value


class AuthorGate:
    code = "ticket_schema"

    def __init__(self, checkout: Checkout, message_class: str = "suggestion", *, remove=shutil.rmtree) -> None:
        self.checkout = checkout
        self.message_class = message_class
        self.message: Message | None = None
        self.copied: dict[str, list[str]] = {}
        self.copied_bytes: dict[str, bytes] = {}
        self.passed_stems: set[str] = set()
        self._remove = remove

    def cleanup(self) -> None:
        """Remove only candidate directories this gate created, through an injected seam."""
        for stem in list(self.copied):
            directory = self.checkout.repo / "tickets" / stem
            if directory.exists():
                self._remove(directory)
            for path in self.copied[stem]:
                self.copied_bytes.pop(path, None)
            del self.copied[stem]

    def check(self, artifact: BaseModel, workspace: Path) -> GateReport:
        assert isinstance(artifact, AuthorReply)
        if self.copied and artifact.stem not in self.copied:
            self.cleanup()
        findings = list(stem_findings(artifact.stem))
        path = ticket_path(artifact.stem)
        roadmap = self.message.roadmap_row if self.message is not None else None
        if roadmap is not None and artifact.stem != roadmap.stem:
            findings.append(Finding(code=self.code, path=path, message=f"roadmap row requires stem {roadmap.stem}", paved_road=f"use the row's stem {roadmap.stem}"))
        existing = self.checkout.repo / path if roadmap is not None else self.checkout.repo / "tickets" / artifact.stem
        if existing.exists() and artifact.stem not in self.copied:
            findings.append(Finding(code=self.code, path=path, message=f"stem {artifact.stem!r} already exists", paved_road="choose a new, never-before-used ticket stem"))
        if artifact.stem not in self.passed_stems and any(event.ticket == artifact.stem for event in self.checkout.journal.read()):
            findings.append(Finding(code=self.code, path=path, message=f"stem {artifact.stem!r} is already named in the journal", paved_road="choose a new, never-before-used ticket stem"))
        try:
            message = self.message
            if message is not None and message.report is not None and not findings:
                # Reserve ownership before writing so partial copies unwind too.
                paths = self.copied.setdefault(artifact.stem, [])
                for kind in CAPS:
                    if (source := getattr(message.report.custody, kind)) is not None:
                        data = bounded(self.checkout.config.state_dir / BOX_DIR, source, kind)
                        target = f"tickets/{artifact.stem}/evidence/" + ("replay.json" if kind == "replay" else "log.txt")
                        self.checkout.fs.write(self.checkout.repo / target, data)
                        self.copied_bytes[target] = data
                        if target not in paths:
                            paths.append(target)
                report_path = f"tickets/{artifact.stem}/evidence/report.json"
                data = message.report.report.model_dump_json().encode()
                self.checkout.fs.write(self.checkout.repo / report_path, data)
                self.copied_bytes[report_path] = data
                if report_path not in paths:
                    paths.append(report_path)
            candidate = artifact.ticket
            if split_frontmatter(candidate) is not None:
                candidate = stamp(stamp(candidate, "source", f"box:{self.message_class}"), "state", "draft")
            parsed = validate_ticket(artifact.stem, candidate, self.checkout.repo)
            if roadmap is not None:
                if "## Goal / Why\n" in candidate:
                    findings.extend(slice_follow_up(roadmap, parsed.sections["Goal / Why"], parsed.scope_fence))
                if "## Scope in / Scope out\n" in candidate:
                    findings.extend(deferral_follow_up(roadmap, parsed.sections["Scope in / Scope out"], parsed.scope_fence, self.checkout.repo))
                for field in ("kind", "priority"):
                    expected = getattr(roadmap, field)
                    if getattr(parsed.frontmatter, field) != expected:
                        findings.append(Finding(code=self.code, path=path, message=f"roadmap row requires {field}: {expected}", paved_road=f"write {field}: {expected}"))
            if message is not None and message.report is not None:
                if parsed.frontmatter.kind != "bug":
                    findings.append(Finding(code=self.code, path=path, message="host report requires kind: bug", paved_road="author a bug ticket with one regression command and carries prefixes"))
                if message.bug_origin == "player" and message.summary in split_frontmatter(candidate)[1]:
                    findings.append(
                        Finding(code=self.code, path=path, message="raw player prose appears in ticket body", paved_road="write your own summary; cite the delimited evidence file instead")
                    )
        except TicketInvalid as exc:
            findings.extend(exc.findings)
        except (OSError, ValueError) as exc:
            findings.append(Finding(code=self.code, path=path, message=f"report custody refused: {exc}", paved_road="repair bounded Box custody before authoring a bug ticket"))
        if findings:
            self.cleanup()
        else:
            self.passed_stems.add(artifact.stem)
        return GateReport(code=self.code, verdict="fail" if findings else "pass", findings=findings)


@dataclass(frozen=True)
class AuthorOutcome:
    stem: str | None = None
    declined: str | None = None


def slice_follow_up(roadmap_row, goal_text: str, fence: tuple[str, ...]) -> list[Finding]:
    from clutch.roadmap import ROADMAP

    if roadmap_row is None or not re.search(r"\bslice\b", goal_text, re.IGNORECASE) or ROADMAP in fence:
        return []
    return [
        Finding(
            code=AuthorGate.code,
            message="roadmap row slice has no follow-up roadmap fence",
            paved_road=f"deliver the whole row, or fence {ROADMAP} and add a follow-up row for the remaining parts in Scope in",
        )
    ]


def deferral_follow_up(roadmap_row, scope_text: str, fence: tuple[str, ...], repo: Path) -> list[Finding]:
    from clutch.roadmap import ROADMAP

    phrase = r"\b(?:separate tickets?|follow-up tickets?|follow-up rows?|later tickets?|future tickets?|another ticket|other tickets)\b"
    if roadmap_row is None or not re.search(phrase, scope_text, re.IGNORECASE) or ROADMAP in fence:
        return []
    if any((repo / ticket_path(stem)).is_file() for stem in re.findall(r"`([a-z0-9][a-z0-9-]{1,63})`", scope_text)):
        return []
    return [
        Finding(
            code=AuthorGate.code,
            message="roadmap row defers work without an existing follow-up ticket",
            paved_road=f"name an existing ticket stem in backticks, or fence {ROADMAP} and add a follow-up row, or deliver the whole row",
        )
    ]


def goal(text: str) -> str:
    after = text.partition("## Goal / Why\n")[2]
    return next((line.strip() for line in after.splitlines() if line.strip()), "")


async def committed(checkout: Checkout, path: Path) -> bool:
    try:
        await checkout.git.rev_parse(checkout.repo, f"HEAD:{path}")
    except GitError:
        return False
    return True


def ticket_state(text: str) -> str | None:
    front = split_frontmatter(text)
    if front is None:
        return None
    try:
        data = yaml.safe_load(front[0])
    except yaml.YAMLError:
        return None
    state = data.get("state") if isinstance(data, dict) else None
    return state if isinstance(state, str) else None


async def is_rejected(checkout: Checkout, stem: str) -> bool:
    if last_states(checkout.journal.read()).get(stem) == "rejected":
        return True
    path = ticket_path(stem)
    try:
        text = await checkout.git._run(checkout.repo, "show", f"HEAD:{path}")
    except GitError:
        return False
    return ticket_state(text) == "rejected"


async def list_open_tickets(checkout: Checkout) -> str:
    states = last_states(checkout.journal.read())
    lines = []
    for path in sorted((checkout.repo / "tickets").glob("*/ticket.md")):
        stem = path.parent.name
        if states.get(stem) not in SETTLED and await committed(checkout, path.relative_to(checkout.repo)) and not await is_rejected(checkout, stem):
            lines.append(f"{stem}: {goal(path.read_text())}")
    return "\n".join(lines)


async def commit_record(checkout: Checkout, driver: Driver, record_id: str, data: bytes) -> None:
    path = record_path(record_id)

    async def edit() -> None:
        checkout.fs.write(checkout.repo / path, data)

    async def commit() -> None:
        await checkout.git.commit_edit(checkout.repo, f"clutch(decisions): {record_id}", only=[str(path)], edit=edit)

    await driver.effects.run(commit, key=f"ticket-plane/decisions/{record_id}", ticket=None)


async def failure_declined(checkout: Checkout, driver: Driver, box: Box, message: Message, evidence: str) -> AuthorOutcome:
    record_id = f"declined-{message.id}"
    record = DecisionRecord(id=record_id, kind="declined", link=message.id, reopen_after_days=30)
    body = f"Author could not produce a ticket.\n\nEvidence: {evidence}\n"
    await commit_record(checkout, driver, record_id, render_record(record, body).encode())
    box.resolve(message.id, Resolution(kind="declined", link=record_id))
    return AuthorOutcome(declined=record_id)


def record_retro_ticket(journal, message: Message, stem: str) -> None:
    if message.message_class != "retro_finding":
        return
    body = {"kind": "retro_ticket_authored", "box_id": message.id, "retro_report_key": message.retro_report_key, "ticket_stem": stem}
    key = f"retro-ticket/{stem}"
    history = journal.read()
    boundary = max(
        (i for i, e in enumerate(history) if e.type == EventType.EFFECT_INTENT and (e.key or "").startswith(f"retro-recurrence/{message.id}/") and e.body.get("reopened") is True), default=-1
    )
    prior = [
        e
        for i, e in enumerate(history)
        if e.key == key or (e.body.get("kind") == "retro_ticket_authored" and (e.body.get("ticket_stem") == stem or (e.body.get("box_id") == message.id and (not message.reopen or i > boundary))))
    ]
    if prior:
        if len(prior) != 1 or prior[0].type != EventType.SIGNAL or prior[0].key != key or prior[0].ticket != stem or prior[0].body != body:
            raise BoxError("conflicting retro ticket provenance; restore the Author-produced bridge before resolving the Box")
        return
    journal.append(EventType.SIGNAL, body, ticket=stem, key=key)


async def recover_retro_ticket(checkout: Checkout, box: Box, message: Message) -> AuthorOutcome | None:
    """Finish the bridge/resolution crash window without another Author invocation."""
    if message.message_class != "retro_finding":
        return None
    history = checkout.journal.read()
    boundary = max(
        (i for i, e in enumerate(history) if e.type == EventType.EFFECT_INTENT and (e.key or "").startswith(f"retro-recurrence/{message.id}/") and e.body.get("reopened") is True), default=-1
    )
    stems = set()
    for event in history[boundary + 1 :]:
        parts = (event.key or "").split("/")
        if event.type != EventType.EFFECT_COMPLETION or len(parts) != 6 or parts[:2] != ["llm", "author"] or parts[3:5] != ["author", str(message.seq)]:
            continue
        try:
            proposal = AuthorReply.model_validate_json(unwrap_fence(event.body["result"]["text"]))
        except ValueError:
            continue
        commit = next((e for e in history if e.type == EventType.EFFECT_COMPLETION and e.key == f"ticket-plane/{proposal.stem}/author"), None)
        if commit is not None:
            text = await checkout.git._run(checkout.repo, "show", f"{commit.body['result']}:{ticket_path(proposal.stem)}")
            if validate_ticket(proposal.stem, text, checkout.repo).frontmatter.source != "box:retro_finding":
                raise BoxError("conflicting committed retro ticket source; restore the Author-produced ticket and bridge")
            stems.add(proposal.stem)
    if not stems:
        return None
    if len(stems) != 1:
        raise BoxError("conflicting retro author completions; restore the unique Author-produced ticket provenance")
    stem = stems.pop()
    record_retro_ticket(checkout.journal, message, stem)
    box.resolve(message.id, Resolution(kind="ticket", link=stem))
    return AuthorOutcome(stem=stem)


async def author(checkout: Checkout, driver: Driver, box: Box, message: Message, pass_no: int) -> AuthorOutcome:
    """Author and ticket-plane commit one recorded author verdict."""
    try:
        row = policy_row(message.message_class, message.bug_origin, message.has_repro)
    except ValueError as exc:
        return await failure_declined(checkout, driver, box, message, str(exc))
    assert message.verdict is not None
    tracked = await checkout.git.ls_files(checkout.repo)
    if message.message_class == "retro_finding":
        untracked = [f"clutch/{path}" for path in message.proposed_spec_paths if f"clutch/{path}" not in tracked]
        if untracked:
            evidence = f"Untracked spec paths: {', '.join(untracked)}; retro report: {message.retro_report_key}. The clutch install owns these specs; the owner should carry the proposal to clutch."
            return await failure_declined(checkout, driver, box, message, evidence)
    roadmap = message.roadmap_row
    plan = "none"
    if roadmap is not None:
        if roadmap.plan not in tracked:
            return await failure_declined(checkout, driver, box, message, f"Untracked plan {roadmap.plan} for roadmap row {roadmap.number} ({roadmap.stem})")
        plan = plan_excerpt((checkout.repo / roadmap.plan).read_text())
    files = "\n".join(tracked)
    spec: Spec = load_spec((SPECS_DIR / "author.md").read_text())
    try:
        report = report_data(message.report, box.root) if message.report else None
    except (OSError, ValueError) as exc:
        return await failure_declined(checkout, driver, box, message, f"report custody refused: {exc}")
    request = json.dumps(
        {
            "class": message.message_class,
            "rationale": message.verdict.rationale,
            "summary": message.summary,
            "retro_report_key": message.retro_report_key,
            "fixed_failure": message.fixed_failure,
            "overcorrection_risk": message.overcorrection_risk,
            "proposed_spec_paths": [f"clutch/{path}" for path in message.proposed_spec_paths],
            "test_issue": message.test_issue,
            "conflict_action": message.conflict_action,
            "proposed_paths": message.proposed_paths,
            "reopen": message.reopen,
            "report": report,
        }
    )

    collected: list[Finding] = []

    def collect(findings: list[Finding]) -> None:
        for finding in findings:
            if not any((old.code, old.message) == (finding.code, finding.message) for old in collected):
                collected.append(finding)

    def render_author(_: object, findings: list) -> str:
        collect(findings)
        inputs = {
            "guide": (Path(__file__).parent / "docs" / "host-authoring.md").read_text(),
            "skeletons": "\n".join(f"{kind}:\n{template(kind)}" for kind in KINDS),
            "calibration": estimates,
            "request": request,
            "roadmap_row": roadmap.model_dump_json() if roadmap is not None else "none",
            "plan": plan,
            "context_suggest": suggestions,
            "neighbors": neighbor_block,
            "files": files,
            "open_tickets": open_tickets,
            "retry_findings": findings_text(findings),
            "previous_reply": previous_reply if previous_reply is not None else "none",
        }
        return render(spec, inputs)

    open_tickets = await list_open_tickets(checkout)
    estimates = calibration.render(calibration.latest(checkout.journal.read()))
    suggestions = context_block(checkout.config.state_dir, roadmap.content if roadmap is not None else message.summary + "\n" + message.verdict.rationale, roadmap.stem if roadmap is not None else "")
    neighbor_block = await neighbors_block(checkout, roadmap.content if roadmap is not None else message.summary, message.id, exclude_refs=(f"row {roadmap.number}",) if roadmap is not None else ())
    previous_reply: str | None = None
    next_unused = 1
    reviewed: RequisitionVerdict | None = None
    reviewed_text: str | None = None
    reviewed_state: str | None = None
    author_gate = AuthorGate(checkout, message.message_class)
    author_gate.message = message

    async def review_candidate(artifact: BaseModel, call_seq: int) -> GateReport:
        nonlocal reviewed, reviewed_text, reviewed_state, next_unused, previous_reply
        assert isinstance(artifact, AuthorReply)
        previous_reply = artifact.ticket
        if author_gate.check(artifact, checkout.repo).verdict == "fail":
            # Grammar-invalid candidates never spend a requisition review call.
            return GateReport(code="requisition_review", verdict="pass")
        provisional = stamp(stamp(artifact.ticket, "source", f"box:{message.message_class}"), "state", "draft")
        parsed = validate_ticket(artifact.stem, provisional, checkout.repo)
        state = start_state(
            checkout.config,
            row=row,
            fence=parsed.scope_fence,
            gate_bypass=parsed.frontmatter.gate_bypass,
            go=resolve_baseline(checkout.config, checkout.journal.read(), specs_dir=SPECS_DIR).binds,
            reopen=message.reopen,
        )
        text = stamp(provisional, "state", state)
        start = max(call_seq, next_unused)
        reviewed = await review_with_identity(
            driver,
            git=checkout.git,
            config=checkout.config,
            history=checkout.journal.read(),
            repo=checkout.repo,
            stem=artifact.stem,
            text=text,
            specs_dir=SPECS_DIR,
            coverage_map=checkout.config.state_dir / "coverage-map.json" if checkout.config.review.coverage_map is not None else None,
            tier=checkout.config.routing_default_tier,
            stem_slot="author",
            run_seq=pass_no,
            attempt=message.seq,
            call_seq=start,
            expected_budget=AUTHOR_STUCK_S / 2,
            prior=FIRST_REVIEW if reviewed is None else render_prior_review(reviewed.verdict, [f.model_dump() for f in reviewed.findings], reviewed_text, text),
        )
        next_unused = start + reviewed.calls
        reviewed_text = text
        reviewed_state = state
        findings = reviewed.findings
        if reviewed.verdict != "approve":
            author_gate.cleanup()
        if reviewed.verdict == "rma":
            findings = [finding.model_copy(update={"code": "requisition_rma"}) for finding in findings]
        return GateReport(code="requisition_review", verdict="pass" if reviewed.verdict == "approve" else "fail", findings=findings)

    checkout.journal.append(EventType.SIGNAL, {"signal": "author_invoked", "message": message.id})
    try:
        result = await driver.run(
            LlmStage(surface="author", emits=AuthorReply, gates=[author_gate], render=render_author, review=review_candidate, terminal_findings=frozenset({"requisition_rma"})),
            None,
            ticket=None,
            subject=message.id,
            run_seq=pass_no,
            attempt=message.seq,
            workspace=checkout.repo,
            tier=checkout.config.routing_default_tier,
            effort=spec.meta.effort,
            stuck_budget=AUTHOR_STUCK_S,
            expected_budget="surface",
            scope_fence=(),
        )
    except BaseException:
        author_gate.cleanup()
        raise
    if result.outcome != "ok" or not isinstance(result.artifact, AuthorReply):
        author_gate.cleanup()
        collect(result.findings)
        return await failure_declined(checkout, driver, box, message, findings_text(collected) or result.outcome)
    reply = result.artifact
    assert reviewed is not None and reviewed_text is not None and reviewed_state is not None
    text = reviewed_text
    path = ticket_path(reply.stem)

    paths = [path, *author_gate.copied.get(reply.stem, [])]
    prior: dict[str, bytes | None] = {}
    published: dict[str, bytes] = {}
    copied: dict[str, bytes] = {}

    async def publish() -> None:
        target = checkout.repo / path
        if target.exists() and reply.stem not in author_gate.copied:
            raise ValueError(f"stem {reply.stem!r} was claimed since the gate check")
        validate_ticket(reply.stem, text, checkout.repo)
        prior[path] = target.read_bytes() if target.exists() else None
        published[path] = text.encode()
        checkout.fs.write(target, published[path])

    async def commit() -> str:
        return await checkout.git.commit_edit(checkout.repo, f"clutch({reply.stem}): ticket", only=paths, edit=publish)

    async def compensate() -> None:
        # A landed commit survives a failed SHA read or Effects completion.
        for name, output in {**copied, **published}.items():
            target = checkout.repo / name
            if not target.exists() or target.read_bytes() != output:
                continue
            committed_sha = (await checkout.git._run(checkout.repo, "ls-tree", "--format=%(objectname)", "HEAD", "--", name)).strip()
            if committed_sha == blob_sha(output):
                continue
            before = prior.get(name)
            if before is None:
                target.unlink()
            else:
                checkout.fs.write(target, before)
        directory = checkout.repo / "tickets" / reply.stem
        for folder in (directory / "evidence", directory):
            if folder.exists() and not any(folder.iterdir()):
                folder.rmdir()

    try:
        # Private evidence preparation must retain publication's failure handling.
        for name in author_gate.copied.get(reply.stem, []):
            copied[name] = author_gate.copied_bytes[name]
            if (checkout.repo / name).read_bytes() != copied[name]:
                raise ValueError(f"evidence {name!r} changed since the gate check")
        if roadmap is not None:
            evidence = await checkout.git._run(checkout.repo, "ls-files", "--cached", "--others", "--exclude-standard", "-z", "--", f"tickets/{reply.stem}/evidence/")
            paths.extend(p for p in evidence.split("\0") if p and p not in paths)
        sha = await driver.effects.run(commit, key=f"ticket-plane/{reply.stem}/author", ticket=None)
    except BaseException as exc:
        # Gate output identifies owned bytes even when snapshot reads fail.
        for name in author_gate.copied.get(reply.stem, []):
            if name not in copied:
                copied[name] = author_gate.copied_bytes[name]
        if copied or published:
            try:
                await checkout.git.commit_edit(checkout.repo, f"clutch({reply.stem}): compensate author", only=paths, edit=compensate)
            except NothingToCommit:
                pass
        author_gate.copied.clear()
        if not isinstance(exc, Exception):
            raise
        return await failure_declined(checkout, driver, box, message, f"commit failed: {type(exc).__name__}: {exc}")
    author_gate.copied.clear()
    checkout.journal.append(EventType.SIGNAL, {"signal": "ticket_intake", "source": f"box:{message.message_class}", "state": reviewed_state, "new": True, "commit": sha}, ticket=reply.stem)
    checkout.journal.append(
        EventType.SIGNAL,
        {
            "signal": "requisition_verdict",
            "verdict": "approve",
            "ticket_sha": reviewed.ticket_sha,
            "provider": reviewed.provider,
            "model": reviewed.model,
            "spec_version": reviewed.spec_version,
            "input_identity": reviewed.input_identity,
        },
        ticket=reply.stem,
    )
    record_retro_ticket(checkout.journal, message, reply.stem)
    box.resolve(message.id, Resolution(kind="ticket", link=reply.stem))
    return AuthorOutcome(stem=reply.stem)
