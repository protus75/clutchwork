"""Review release promises against merged code and record uncovered work as roadmap rows."""

import json
import re
from collections import Counter
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from clutch import meta, providers, roadmap
from clutch.artifacts import Finding, NonBlank
from clutch.box import BOX_DIR, Box
from clutch.driver import LlmStage
from clutch.gates import GateReport
from clutch.journal import EventType
from clutch.runner import SPECS_DIR, Refusal
from clutch.specs import load_spec, render
from clutch.stages import findings_text
from clutch.status import last_states
from clutch.tickets import stem_findings, ticket_path

ACCEPT_STUCK_S = 1800.0


class GapRow(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    stem: NonBlank
    kind: Literal["feature", "chore"]
    owner: NonBlank
    content: NonBlank


class Promise(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    promise: NonBlank
    source: NonBlank
    status: Literal["met", "partial", "unmet", "deferred"]
    evidence: Annotated[list[NonBlank], Field(min_length=1)]
    decision: NonBlank | None
    row: Annotated[int, Field(ge=1)] | None
    new_row: GapRow | None

    @model_validator(mode="after")
    def _coherent(self):
        count = sum(value is not None for value in (self.decision, self.row, self.new_row))
        if self.status == "met":
            valid = count == 0
        elif self.status in {"partial", "unmet"}:
            valid = self.decision is None and count == 1
        else:
            valid = count == 1
        if not valid:
            raise ValueError("met has no gap; partial/unmet need exactly one row or new_row; deferred needs exactly one decision, row or new_row")
        return self


class AcceptanceReply(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    promises: Annotated[list[Promise], Field(min_length=1)]


async def accept(checkout, driver, release) -> tuple[bool, list[str]]:
    repo = checkout.repo
    path = repo / roadmap.ROADMAP
    road = f"repair {roadmap.ROADMAP}, then run `clutch roadmap accept {release}` again"
    if not path.is_file():
        raise Refusal(f"missing {roadmap.ROADMAP}", road)
    if await checkout.git.status_porcelain(repo, "--", roadmap.ROADMAP):
        raise Refusal(f"uncommitted {roadmap.ROADMAP}", f"commit or restore {roadmap.ROADMAP}, then run `clutch roadmap accept {release}` again")
    text = path.read_text()
    rows = roadmap.parse(text)
    selected = [row for row in rows if roadmap.release_name(row.release) == release]
    if not selected:
        raise Refusal(f"no release {release}", road)
    release_plan = next((line for line in text.splitlines() if line.startswith(f"| **{release}** |")), None)
    if release_plan is None:
        raise Refusal(f"no section 1 row for {release}", road)
    events = checkout.journal.read()
    states = last_states(events)
    files = set((await checkout.git._run(repo, "ls-files", "--cached", "--others", "--exclude-standard", "-z")).split("\0"))
    strikes = roadmap.choose(rows, states=states, files=files).strike
    messages = Box(checkout.config.state_dir / BOX_DIR, checkout.fs).messages()
    latest = {message.roadmap_row.stem: message for message in messages if message.roadmap_row is not None}
    row_states = {}
    for row in rows:
        message = latest.get(row.stem)
        if row.struck or row in strikes:
            state = "merged"
        elif states.get(row.stem) == "rejected":
            state = "rejected"
        elif message is not None and message.resolution is not None and message.resolution.kind == "declined":
            state = "declined"
        elif row.linked or str(ticket_path(row.stem)) in files:
            state = "authored"
        else:
            state = "open"
        row_states[row.number] = state
    plans = sorted({roadmap.ROADMAP} | {plan for row in selected if (plan := roadmap.plan_path(row.owner, files)) is not None})
    releases = list(dict.fromkeys(roadmap.release_name(row.release) for row in rows))
    index = releases.index(release)
    next_release = releases[index + 1] if index + 1 < len(releases) else None
    spec = load_spec((SPECS_DIR / "acceptance.md").read_text())
    stems = set()
    for row in selected:
        if row_states[row.number] == "merged":
            stems.add(row.stem)
            stems.update(re.findall(r"tickets/([^/]+)/", row.content))
    counts = Counter()
    for event in events:
        parts = event.key.split("/") if event.key else []
        if event.type == EventType.EFFECT_COMPLETION and len(parts) == 6 and parts[0] == "llm" and parts[1] in stems and parts[3] == "implement":
            provider = event.body.get("cost", {}).get("provider")
            if provider is not None:
                counts[provider] += 1
    implementer = counts.most_common(1)[0][0] if counts else None
    other = next((p.name for p in checkout.config.providers if p.name != implementer), None)
    if implementer is not None and other is not None and any(c.provider.name == implementer for c in providers.candidates(checkout.config, spec.meta.tier, "acceptance")):
        raise Refusal(
            f"acceptance judge {implementer} implemented most of release {release}",
            f"route the judge to another provider: {{tier: {spec.meta.tier}, surface: acceptance, candidates: [{{provider: {other}}}]}}",
        )
    release_data = dict(release=release, next_release=next_release, release_plan=release_plan, plans=plans)
    row_data = [
        dict(
            number=row.number,
            release=roadmap.release_name(row.release),
            stem=row.stem,
            owner=row.owner,
            kind=row.kind,
            priority=row.priority,
            depends=row.depends,
            content=row.content,
            state=row_states[row.number],
        )
        for row in rows
    ]

    def render_reply(consumed, findings):
        return render(spec, {"release": json.dumps(release_data), "rows": json.dumps(row_data), "retry_findings": findings_text(findings)})

    async def review(reply, n):
        errors = []

        def fail(message, paved_road):
            errors.append(Finding(code="acceptance_reply", message=message, paved_road=paved_road))

        used = {row.stem for row in rows} | set(states) | {p.split("/")[1] for p in files if p.startswith("tickets/") and len(p.split("/")) > 2}
        by_number = {row.number: row for row in rows}
        for promise in reply.promises:
            source = promise.source.split("#", 1)[0]
            if source not in plans:
                fail(f"unknown source {promise.source}", "cite a path in the release plans")
            target = next_release if promise.status == "deferred" else release
            if promise.row is not None:
                row = by_number.get(promise.row)
                if row is None:
                    fail(f"unknown row {promise.row}", "name a section 8 row number")
                else:
                    if roadmap.release_name(row.release) != target:
                        fail(f"row {promise.row} is in the wrong release", f"name an open or authored row in {target}")
                    if row_states[row.number] in {"merged", "rejected", "declined"}:
                        fail(f"row {promise.row} is {row_states[row.number]}", "propose a replacement new_row whose Content names the row it replaces")
            if promise.status == "deferred" and (promise.row is not None or promise.new_row is not None) and next_release is None:
                fail("no next release", "cite a recorded decision or add a next release before deferring work")
            if gap := promise.new_row:
                for finding in stem_findings(gap.stem):
                    fail(finding.message, finding.paved_road)
                if gap.stem in used:
                    fail(f"stem {gap.stem} is already used", "choose a stem no row, ticket, journal entry or other new_row uses")
                used.add(gap.stem)
                if "|" in gap.owner or "\n" in gap.owner or "\r" in gap.owner or roadmap.plan_path(gap.owner, files) != source:
                    fail(f"invalid owner {gap.owner}", "use roadmap for the roadmap, otherwise a word from the source plan filename")
                if "\n" in gap.content or "\r" in gap.content:
                    fail("Content contains a newline", "write one-line Content citing the plan section and evidence")
        return GateReport(code="acceptance_reply", verdict="fail" if errors else "pass", findings=errors)

    result = await driver.run(
        LlmStage(surface="acceptance", emits=AcceptanceReply, gates=[], render=render_reply, review=review),
        None,
        ticket=None,
        subject=release,
        run_seq=len(events),
        attempt=1,
        workspace=repo,
        tier=spec.meta.tier,
        effort=spec.meta.effort,
        stuck_budget=ACCEPT_STUCK_S,
        expected_budget="surface",
        scope_fence=(),
    )
    if result.outcome != "ok":
        raise Refusal(f"acceptance review ended {result.outcome}", f"run `clutch roadmap accept {release}` again")
    promises = result.artifact.promises
    added = {}
    if any(p.new_row is not None for p in promises):

        async def edit():
            if await checkout.git.status_porcelain(repo, "--", roadmap.ROADMAP):
                raise Refusal(f"uncommitted {roadmap.ROADMAP}", f"commit or restore {roadmap.ROADMAP}, then run `clutch roadmap accept {release}` again")
            text = path.read_text()
            tracked = await checkout.git.ls_files(repo)
            sha = await checkout.git.rev_parse(repo, "HEAD")
            selected_meta = list(meta._files(checkout.config, tracked, (roadmap.ROADMAP,)))
            if selected_meta:
                try:
                    meta.parse(text, path.suffix)
                except meta.Malformed as exc:
                    raise Refusal(f"malformed {roadmap.ROADMAP}", f"fix the meta block, then run `clutch roadmap accept {release}` again") from exc
            number = max(row.number for row in roadmap.parse(text))
            for promise in promises:
                if gap := promise.new_row:
                    number += 1
                    target = next_release if promise.status == "deferred" else release
                    line = f"| {number} | `{gap.stem}` | {gap.owner} | {gap.kind} | P1 | | | {gap.content} |"
                    text = roadmap.append_row(text, target, line)
                    added[gap.stem] = (number, target)
            if selected_meta:
                fields, body, offset = meta.parse(text, path.suffix)
                fields, generated_relates = meta.generated(fields, body, roadmap.ROADMAP, selected_meta[0][1], tracked, sha)
                text, _ = meta.compose(fields, body, offset, path.suffix, trim=generated_relates)
            checkout.fs.write(path, text.encode())

        await checkout.git.commit_edit(repo, f"clutch(roadmap): accept {release}", only=[roadmap.ROADMAP], edit=edit)
    lines = []
    by_number = {row.number: row for row in rows}
    for promise in promises:
        suffix = ""
        if promise.decision is not None:
            suffix = f" -- {promise.decision}"
        elif promise.row is not None:
            suffix = f" -- row {promise.row} {by_number[promise.row].stem}"
        elif promise.new_row is not None:
            number, target = added[promise.new_row.stem]
            suffix = f" -- new row {number} {promise.new_row.stem} in {target}"
        lines.append(f"accept {release}: {promise.status}: {promise.promise} [{promise.source}]{suffix}")
    failed = sum(p.status in {"partial", "unmet"} for p in promises)
    lines.append(
        f"accept {release}: failed: {failed} of {len(promises)} promises partial or unmet -- `clutch roadmap author` files the rows above; the gate passes once they merge"
        if failed
        else f"accept {release}: passed"
    )
    return not failed, lines
