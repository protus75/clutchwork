"""Fill generated metadata from a read-only model reply."""

import json
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from clutch import meta
from clutch.artifacts import Finding
from clutch.driver import LlmStage
from clutch.gates import GateReport
from clutch.specs import RenderOverBound, render
from clutch.stages import findings_text


class MetaEntry(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    purpose: str
    relates: list[str]
    owner: str


class MetaReply(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    files: dict[str, MetaEntry]


def review_reply(expected_paths, reply):
    expected, actual = set(expected_paths), set(reply.files)
    findings = [Finding(code="meta_reply", message=f"missing path: {p}", paved_road="Return exactly the requested paths.") for p in sorted(expected - actual)]
    findings += [Finding(code="meta_reply", message=f"extra path: {p}", paved_road="Return exactly the requested paths.") for p in sorted(actual - expected)]
    return GateReport(code="meta_reply", verdict="fail" if findings else "pass", findings=findings)


def make_ask(driver, spec, repo, run_seq):
    async def ask(paths, files_json):
        ask.attempt += 1

        async def review(reply, n):
            return review_reply(paths, reply)

        result = await driver.run(
            LlmStage(surface="meta", emits=MetaReply, gates=[], render=lambda consumed, findings: render(spec, {"files": files_json, "retry_findings": findings_text(findings)}), review=review),
            None,
            ticket=None,
            subject=f"{len(paths)}-files",
            run_seq=run_seq,
            attempt=ask.attempt,
            workspace=repo,
            tier=spec.meta.tier,
            effort=spec.meta.effort,
            stuck_budget=3000.0,
            expected_budget="surface",
            scope_fence=(),
        )
        ask.outcome = result.outcome
        return result.artifact if result.outcome == "ok" else None

    ask.attempt = 0
    ask.outcome = "infra_error"
    return ask


def _line(value):
    return bool(value.strip()) and not any(c in value for c in ("\n", "\r", "-->"))


async def fill(config, root, fs, tracked, sha, spec, ask, paths=()):
    findings = meta.check(config, root, fs, tracked, sha, paths)
    rejected = [(p, reason) for p, reason in findings if reason == "malformed"]
    targets = {p for p, reason in findings if reason in {"missing", "empty_purpose"}}
    kinds = dict(meta._files(config, tracked, paths))
    written = []
    for path in sorted({p for p, reason in findings if reason == "drifted"} - targets):
        text = fs.read_bytes(root / path).decode()
        suffix = Path(path).suffix
        fields, body, offset = meta.parse(text, suffix)
        fields["verified"], fields["hash"] = sha[:8], meta.digest(body)
        composed, _ = meta.compose(fields, body, offset, suffix)
        # Keep all original lines except the two generated values, including formatting.
        prefix = "" if suffix == ".md" else "# "
        replacements = {line.split(":", 1)[0]: line for line in composed[offset:].splitlines(keepends=True)[:8] if line.startswith((prefix + "verified:", prefix + "hash:"))}
        lines = text.splitlines(keepends=True)
        start = len(text[:offset].splitlines(keepends=True))
        for i in range(start + 1, start + 8):
            key = lines[i].split(":", 1)[0]
            if key in replacements:
                lines[i] = replacements[key]
        result = "".join(lines)
        if result != text:
            fs.write(root / path, result.encode())
            written.append(path)
    targets = sorted(targets)
    for start in range(0, len(targets), 20):
        batch = targets[start : start + 20]
        prepared = {}
        payload = []
        for path in batch:
            text = fs.read_bytes(root / path).decode()
            suffix = Path(path).suffix
            fields, body, offset = meta.parse(text, suffix)
            fields, generated_relates = meta.generated(fields, body, path, kinds[path], tracked, sha)
            prepared[path] = (text, body, offset, suffix, fields, generated_relates)
            payload.append({"path": path, "content": body, "fields": fields})
        try:
            reply = await ask(batch, json.dumps(payload))
        except RenderOverBound:
            rejected.extend((path, "render_over_bound") for path in batch)
            continue
        if reply is None:
            rejected.extend((path, getattr(ask, "outcome", "infra_error")) for path in batch)
            continue
        report = review_reply(batch, reply)
        if report.verdict != "pass":
            rejected.extend((path, "invalid_artifact") for path in batch)
            continue
        for path in batch:
            text, body, offset, suffix, fields, generated_relates = prepared[path]
            entry = reply.files[path]
            reason = None
            if not _line(entry.purpose):
                reason = "invalid purpose"
            elif any(p not in tracked or not _line(p) for p in entry.relates):
                reason = "invalid relates"
            elif entry.owner.strip() and not _line(entry.owner):
                reason = "invalid owner"
            if reason:
                rejected.append((path, reason))
                continue
            fields["purpose"] = entry.purpose.strip()
            if not fields["relates"]:
                fields["relates"] = entry.relates
                generated_relates = True
            if fields["owner"] == "engine" and entry.owner.strip():
                fields["owner"] = entry.owner.strip()
            fields["verified"], fields["hash"] = sha[:8], meta.digest(body)
            result, _ = meta.compose(fields, body, offset, suffix, trim=generated_relates)
            if result != text:
                fs.write(root / path, result.encode())
                written.append(path)
    return written, rejected
