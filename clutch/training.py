"""Rebuild training examples from evidence and merged ticket commits."""

import fnmatch
import hashlib
import json
import re
import shlex
from pathlib import PurePosixPath

import duckdb
from pydantic import TypeAdapter, ValidationError

from clutch.config import training_exclude
from clutch.driver import unwrap_fence
from clutch.evidence import antigravity, claude, codex
from clutch.evidence.store import SKIP
from clutch.git import GitError
from clutch.llm import LLMRequest
from clutch.tickets import DIAGNOSIS_FILE, Source, artifact_path, read_tolerant, stem_findings, ticket_path

NOTICE = "Notice: model outputs come from third-party providers whose terms may restrict training other models on them. Check each provider's terms before training on this export."
_SECRET = re.compile(r"AKIA[A-Z0-9]{16}|-----BEGIN [^\n]*PRIVATE KEY-----|Bearer\s+[A-Za-z0-9._~+/=-]{20,}")
_NEGATIVE = {"logic", "acceptance", "scope", "leak"}


def report(counts):
    return [
        NOTICE,
        (
            f"implement: {counts['implement']}, preference: {counts['preference']}, review: {counts['review']}, diagnosis: {counts['diagnosis']}, ticket: {counts['ticket']}, "
            f"conflict: {counts['conflict']}, triage: {counts['triage']}, "
            f"dropped: {counts['dropped']}, skipped: {counts['skipped']}, held-out stems: {counts['heldout']}"
        ),
    ]


def index_files(database, size, connect=duckdb.connect):
    """Read the optional index without changing it."""
    try:
        size(database)
        conn = connect(str(database), read_only=True)
    except OSError, duckdb.Error:
        return {}
    try:
        files = conn.execute("SELECT path, purpose FROM files WHERE path IS NOT NULL").fetchall()
        touches = conn.execute("SELECT path, ticket FROM touches WHERE path IS NOT NULL AND ticket IS NOT NULL").fetchall()
        tickets = {}
        for path, ticket in touches:
            tickets.setdefault(path, set()).add(ticket)
        return {path: (purpose or "", frozenset(tickets.get(path, ()))) for path, purpose in files}
    except duckdb.Error:
        return {}
    finally:
        conn.close()


def _file_purposes(diff, stem, index):
    paths = set()
    for line in diff.splitlines():
        if not line.startswith("diff --git "):
            continue
        try:
            parts = shlex.split(line)
        except ValueError:
            continue
        if len(parts) == 4 and parts[:2] == ["diff", "--git"] and parts[2].startswith("a/") and parts[3].startswith("b/"):
            paths.add(parts[3][2:])
    return [{"path": path, "purpose": index[path][0], "touches": len(index[path][1] - {stem})} for path in sorted(paths) if path in index]


def _safe(record, diffs, redactor, config):
    text = json.dumps(record, ensure_ascii=True)
    if redactor.scrub(text) != text or _SECRET.search(text):
        return False
    for diff in diffs:
        for line in diff.splitlines():
            if not line.startswith("diff --git"):
                continue
            try:
                parts = shlex.split(line)
            except ValueError:
                return False
            if len(parts) != 4 or parts[:2] != ["diff", "--git"] or not parts[2].startswith("a/") or not parts[3].startswith("b/"):
                return False
            for path in (parts[2][2:], parts[3][2:]):
                if not path or any(fnmatch.fnmatchcase(path, glob) or fnmatch.fnmatchcase(PurePosixPath(path).name, glob) for glob in training_exclude(config)):
                    return False
    return True


def _trajectory(store, key, start, config):
    normalizer = {"ClaudeAdapter": claude.normalize, "CodexAdapter": codex.normalize, "AntigravityAdapter": antigravity.normalize}.get(start.provider.adapter)
    if normalizer is None:
        return None
    try:
        end = store.read_record(key, "end")
        if end is SKIP:
            return None
        stdout = store.get_blob(end.raw.stdout)
    except FileNotFoundError:
        return None
    events = normalizer(stdout, times_ns=None, put_blob=lambda data: hashlib.sha256(data).hexdigest())
    result = []
    for event in events:
        if event.kind != "tool_call":
            continue
        paths = event.args or {}
        values = [paths.get(k) for k in ("file_path", "path", "paths", "notebook_path", "Path")]
        paths = [path for value in values for path in (value if isinstance(value, list) else [value]) if isinstance(path, str)]
        if any(fnmatch.fnmatchcase(path, glob) or fnmatch.fnmatchcase(PurePosixPath(path).name, glob) for path in paths for glob in training_exclude(config)):
            continue
        result.append({"seq": event.seq, "tool": event.tool.class_, "native": event.tool.native, "args": event.args})
    return result


def _reply_text(store, key, start):
    normalizer = {"ClaudeAdapter": claude.normalize, "CodexAdapter": codex.normalize, "AntigravityAdapter": antigravity.normalize}[start.provider.adapter]
    end = store.read_record(key, "end")
    if end is SKIP:
        raise ValueError("missing end")
    blobs = {}

    def capture(data):
        digest = hashlib.sha256(data).hexdigest()
        blobs[digest] = data
        return digest

    events = normalizer(store.get_blob(end.raw.stdout), times_ns=None, put_blob=capture)
    messages = [blobs[event.text_blob].decode() for event in events if event.kind == "message" and event.role == "assistant"]
    return "".join(messages) if start.provider.adapter == "AntigravityAdapter" else messages[-1]


def _calls(store, keys, surface="implement"):
    calls = []
    for key in keys:
        try:
            start = store.read_record(key, "start")
        except FileNotFoundError:
            continue
        if start is not SKIP and start.surface == surface:
            try:
                run = int(start.run_seq)
            except ValueError:
                continue
            calls.append((run, start.attempt, start.call, key, start))
    return sorted(calls, key=lambda item: item[:4])


def _identity(start, keys, stem, label, kind):
    return dict(
        kind=kind,
        stem=stem,
        group=stem,
        run_seq=int(start.run_seq),
        attempt=start.attempt,
        call_keys=keys,
        engine_version=start.engine.version,
        spec=start.engine.spec,
        spec_version=start.engine.spec_version,
        label=label,
    )


async def render(
    store, git, repo, redactor, config, read_bytes, kinds=("implement", "preference", "review", "diagnosis"), holdout=0, trajectory=True, since=None, *, only=None, index=None, box_messages=()
):
    counts = dict(implement=0, preference=0, review=0, diagnosis=0, ticket=0, conflict=0, triage=0, dropped=0, skipped=0, heldout=0)
    records = {kind: [] for kind in kinds}
    merged = {stem: sha for sha, stem in await git.merged_tickets(repo)}
    attempts = store.attempts()
    keys = store.call_keys("llm/")
    call_stems = {parts[1] for key in keys if len(parts := key.split("/")) == 6 and parts[3] in ("diagnose", "resolve", "triage")}
    stems = set(merged) | {stem for stem, _, _ in attempts} | call_stems
    ticket_calls = {}
    if "ticket" in records:
        for _, _, _, key, start in _calls(store, keys, "author"):
            try:
                reply = _reply_text(store, key, start)
                stem = json.loads(reply)["stem"]
                if not isinstance(stem, str) or stem_findings(stem):
                    raise ValueError("invalid stem")
                content = read_bytes(repo / ticket_path(stem)).decode()
                source = TypeAdapter(Source).validate_python(read_tolerant(content).frontmatter.get("source"))
                if source == "seed":
                    raise ValueError("seed ticket")
                prompt = store.get_blob(start.prompt.blob).decode()
                ticket_calls[stem] = (key, start, content, prompt, "human" if source == "human" else "author")
            except FileNotFoundError, ValueError, UnicodeError, KeyError, IndexError, TypeError, ValidationError:
                counts["skipped"] += 1
        stems.update(ticket_calls)
    held = sorted(stem for stem in stems if only is None and int(hashlib.sha256(stem.encode()).hexdigest(), 16) % 100 < holdout)
    counts["heldout"] = len(held)
    held_set = set(held) if only is None else stems - only
    diffs = {}
    for stem, sha in sorted(merged.items()):
        if stem in held_set:
            continue
        try:
            diff = await git.diff(repo, f"{sha}^", sha)
            if not diff:
                raise ValueError("empty diff")
            diffs[stem] = diff
            if "implement" in records:
                calls = _calls(store, store.call_keys(f"llm/{stem}/"))
                if not calls:
                    raise ValueError("missing call")
                _, _, _, key, start = calls[-1]
                if since and start.clock.wall_start[:10] < since:
                    continue
                prompt = store.get_blob(start.prompt.blob).decode()
                record = {**_identity(start, [key], stem, "merged", "implement"), "messages": [{"role": "user", "content": prompt}, {"role": "assistant", "content": diff}]}
                if trajectory and (events := _trajectory(store, key, start, config)) is not None:
                    record["trajectory"] = events
                if index and (purposes := _file_purposes(diff, stem, index)):
                    record["file_purposes"] = purposes
                records["implement"].append((record, [diff]))
        except FileNotFoundError, ValueError, UnicodeError, GitError:
            if "implement" in records:
                counts["skipped"] += 1
    for stem, run, attempt in attempts:
        if stem in held_set:
            continue
        manifest = None
        try:
            manifest = store.read_attempt(stem, run, attempt)
            if manifest is not SKIP and "review" in records:
                calls = _calls(store, manifest.call_keys, "review")
                if calls:
                    _, _, _, key, start = calls[-1]
                    if not since or start.clock.wall_start[:10] >= since:
                        prompt = store.get_blob(start.prompt.blob).decode()
                        label = "negative" if any(f.get("code") in _NEGATIVE for f in manifest.findings) else "neutral"
                        content = json.dumps({"outcome": manifest.outcome, "findings": manifest.findings}, sort_keys=True)
                        record = {
                            **_identity(start, manifest.call_keys, stem, label, "review"),
                            "run_seq": run,
                            "attempt": attempt,
                            "messages": [{"role": "user", "content": prompt}, {"role": "assistant", "content": content}],
                        }
                        records["review"].append((record, []))
        except FileNotFoundError, ValueError, UnicodeError:
            counts["skipped"] += int("review" in records)
        if not ({"implement", "preference"} & records.keys()):
            continue
        manifest = None
        try:
            manifest = store.read_attempt(stem, run, attempt)
            if manifest is SKIP:
                continue
            calls = _calls(store, manifest.call_keys)
            if not calls:
                raise ValueError("missing call")
            _, _, _, key, start = min(calls, key=lambda item: item[1:3])
            if since and start.clock.wall_start[:10] < since:
                continue
            prompt = store.get_blob(start.prompt.blob).decode()
            diff = store.get_blob(manifest.diff_blob).decode()
            if not diff:
                raise ValueError("empty diff")
            label = "negative" if any(f.get("code") in _NEGATIVE for f in manifest.findings) else "neutral"
            if "implement" in records:
                record = {
                    **_identity(start, manifest.call_keys, stem, label, "implement"),
                    "run_seq": run,
                    "attempt": attempt,
                    "messages": [{"role": "user", "content": prompt}, {"role": "assistant", "content": diff}],
                }
                if trajectory and (events := _trajectory(store, key, start, config)) is not None:
                    record["trajectory"] = events
                if index and (purposes := _file_purposes(diff, stem, index)):
                    record["file_purposes"] = purposes
                records["implement"].append((record, [diff]))
            if label == "negative" and stem in merged and "preference" in records:
                if stem not in diffs:
                    counts["skipped"] += 1
                else:
                    record = {
                        **_identity(start, manifest.call_keys, stem, label, "preference"),
                        "run_seq": run,
                        "attempt": attempt,
                        "prompt": prompt,
                        "chosen": diffs[stem],
                        "rejected": diff,
                        "reason": "\n".join(f.get("message", "") for f in manifest.findings),
                    }
                    records["preference"].append((record, [diffs[stem], diff]))
        except FileNotFoundError, ValueError, UnicodeError:
            counts["skipped"] += int("implement" in records)
            if "preference" in records and stem in merged and (manifest is None or any(f.get("code") in _NEGATIVE for f in manifest.findings)):
                counts["skipped"] += 1
    if "diagnosis" in records:
        for stem in sorted(stems - held_set):
            calls = _calls(store, store.call_keys(f"llm/{stem}/"), "diagnose")
            if not calls:
                continue
            _, _, _, key, start = calls[-1]
            if since and start.clock.wall_start[:10] < since:
                continue
            try:
                prompt = store.get_blob(start.prompt.blob).decode()
                content = read_bytes(repo / artifact_path(stem, DIAGNOSIS_FILE)).decode()
                record = {
                    **_identity(start, [key], stem, "merged" if stem in merged else "neutral", "diagnosis"),
                    "messages": [{"role": "user", "content": prompt}, {"role": "assistant", "content": content}],
                }
                records["diagnosis"].append((record, []))
            except FileNotFoundError, ValueError, UnicodeError:
                counts["skipped"] += 1
    if "ticket" in records:
        for stem, (key, start, content, prompt, authored_by) in sorted(ticket_calls.items()):
            if stem in held_set or (since and start.clock.wall_start[:10] < since):
                continue
            record = {
                **_identity(start, [key], stem, "merged" if stem in merged else "neutral", "ticket"),
                "authored_by": authored_by,
                "messages": [{"role": "user", "content": prompt}, {"role": "assistant", "content": content}],
            }
            records["ticket"].append((record, []))
    if "triage" in records and "triage" not in held_set:
        messages = {message.seq: message for message in box_messages}
        for run, _, _, key, start in _calls(store, keys, "triage"):
            if key.split("/")[1] != "triage" or (since and start.clock.wall_start[:10] < since):
                continue
            try:
                reply = _reply_text(store, key, start)
                verdict = json.loads(reply)["verdict"]
                if verdict not in ("author", "tombstone", "declined"):
                    raise ValueError("invalid verdict")
                prompt = store.get_blob(start.prompt.blob).decode()
                message = messages.get(run)
                label = "neutral"
                if message is not None and message.status == "resolved":
                    expected = "ticket" if verdict == "author" else verdict
                    label = "merged" if message.resolution.kind == expected else "negative"
                record = {
                    **_identity(start, [key], "triage", label, "triage"),
                    "messages": [{"role": "user", "content": prompt}, {"role": "assistant", "content": reply}],
                }
                records["triage"].append((record, []))
            except FileNotFoundError, ValueError, UnicodeError, KeyError, IndexError, TypeError:
                counts["skipped"] += 1
    if "conflict" in records:
        for key in keys:
            parts = key.split("/")
            if len(parts) != 6 or parts[3] != "resolve" or parts[1] in held_set:
                continue
            stem = parts[1]
            try:
                start = store.read_record(key, "start")
                if start is SKIP or start.surface != "resolve":
                    continue
                if since and start.clock.wall_start[:10] < since:
                    continue
                reply = _reply_text(store, key, start)
                if json.loads(reply)["verdict"] != "resolved":
                    raise ValueError("unresolved")
                prompt = store.get_blob(start.prompt.blob).decode()
                record = dict(
                    kind="conflict",
                    stem=stem,
                    group=stem,
                    run_seq=str(start.run_seq),
                    attempt=start.attempt,
                    call_keys=[key],
                    engine_version=start.engine.version,
                    spec=start.engine.spec,
                    spec_version=start.engine.spec_version,
                    label="merged" if stem in merged else "neutral",
                    messages=[{"role": "user", "content": prompt}, {"role": "assistant", "content": reply}],
                )
                records["conflict"].append((record, []))
            except FileNotFoundError, ValueError, UnicodeError, KeyError, IndexError, TypeError:
                counts["skipped"] += 1
    files = {}
    for kind, items in records.items():
        lines = []
        for record, record_diffs in sorted(items, key=lambda item: (item[0]["stem"], item[0]["run_seq"], item[0]["attempt"])):
            if _safe(record, record_diffs, redactor, config):
                lines.append(json.dumps(record, ensure_ascii=True) + "\n")
                counts[kind] += 1
            else:
                counts["dropped"] += 1
        files["sft.jsonl" if kind == "implement" else f"{kind}.jsonl"] = "".join(lines).encode()
    if holdout and only is None:
        files["holdout.txt"] = "".join(stem + "\n" for stem in held).encode()
    return files, counts


async def evaluate(records, llm, tier):
    counts = dict(total=0, agree=0, disagree=0, unparsed=0)
    for record in records:
        result = await llm.call(LLMRequest(surface="review", rendered=record["messages"][0]["content"], tier=tier, effort="medium", subject=f"eval-{counts['total'] + 1}", worktree=None))
        counts["total"] += 1
        try:
            reply = json.loads(unwrap_fence(result.text))
        except ValueError:
            reply = None
        verdict = reply.get("verdict") if isinstance(reply, dict) else None
        if verdict not in ("approve", "snag", "rma"):
            counts["unparsed"] += 1
        elif (verdict == "snag") == (record["label"] == "negative"):
            counts["agree"] += 1
        else:
            counts["disagree"] += 1
    counts["agreement"] = counts["agree"] / counts["total"] if counts["total"] else 0.0
    return counts


def report_eval(counts):
    return f"total: {counts['total']}, agree: {counts['agree']}, disagree: {counts['disagree']}, unparsed: {counts['unparsed']}, agreement: {counts['agreement']:.2%}"
