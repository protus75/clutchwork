"""Rebuild training examples from evidence and merged ticket commits."""

import fnmatch
import hashlib
import json
import re
import shlex
from pathlib import PurePosixPath

from clutch.evidence import claude, codex, gemini
from clutch.evidence.store import SKIP
from clutch.git import GitError

NOTICE = "Notice: model outputs come from third-party providers whose terms may restrict training other models on them. Check each provider's terms before training on this export."
_SECRET = re.compile(r"AKIA[A-Z0-9]{16}|-----BEGIN [^\n]*PRIVATE KEY-----|Bearer\s+[A-Za-z0-9._~+/=-]{20,}")
_NEGATIVE = {"logic", "acceptance", "scope", "leak"}


def report(counts):
    return [NOTICE, f"implement: {counts['implement']}, preference: {counts['preference']}, dropped: {counts['dropped']}, skipped: {counts['skipped']}, held-out stems: {counts['heldout']}"]


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
                if not path or any(fnmatch.fnmatchcase(path, glob) or fnmatch.fnmatchcase(PurePosixPath(path).name, glob) for glob in config.effective_exclude()):
                    return False
    return True


def _trajectory(store, key, start, config):
    normalizer = {"ClaudeAdapter": claude.normalize, "CodexAdapter": codex.normalize, "GeminiAdapter": gemini.normalize}.get(start.provider.adapter)
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
        values = [paths.get(k) for k in ("file_path", "path", "paths", "notebook_path")]
        paths = [path for value in values for path in (value if isinstance(value, list) else [value]) if isinstance(path, str)]
        if any(fnmatch.fnmatchcase(path, glob) or fnmatch.fnmatchcase(PurePosixPath(path).name, glob) for path in paths for glob in config.effective_exclude()):
            continue
        result.append({"seq": event.seq, "tool": event.tool.class_, "native": event.tool.native, "args": event.args})
    return result


def _calls(store, keys):
    calls = []
    for key in keys:
        try:
            start = store.read_record(key, "start")
        except FileNotFoundError:
            continue
        if start is not SKIP and start.surface == "implement":
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


async def render(store, git, repo, redactor, config, kinds=("implement", "preference"), holdout=0, trajectory=True):
    counts = dict(implement=0, preference=0, dropped=0, skipped=0, heldout=0)
    records = {kind: [] for kind in kinds}
    merged = {stem: sha for sha, stem in await git.merged_tickets(repo)}
    attempts = store.attempts()
    stems = set(merged) | {stem for stem, _, _ in attempts}
    held = sorted(stem for stem in stems if int(hashlib.sha256(stem.encode()).hexdigest(), 16) % 100 < holdout)
    counts["heldout"] = len(held)
    held_set = set(held)
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
                prompt = store.get_blob(start.prompt.blob).decode()
                record = {**_identity(start, [key], stem, "merged", "implement"), "messages": [{"role": "user", "content": prompt}, {"role": "assistant", "content": diff}]}
                if trajectory and (events := _trajectory(store, key, start, config)) is not None:
                    record["trajectory"] = events
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
            if manifest is SKIP:
                continue
            calls = _calls(store, manifest.call_keys)
            if not calls:
                raise ValueError("missing call")
            _, _, _, key, start = min(calls, key=lambda item: item[1:3])
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
    files = {}
    for kind, items in records.items():
        lines = []
        for record, record_diffs in sorted(items, key=lambda item: (item[0]["stem"], item[0]["run_seq"], item[0]["attempt"])):
            if _safe(record, record_diffs, redactor, config):
                lines.append(json.dumps(record, ensure_ascii=True) + "\n")
                counts[kind] += 1
            else:
                counts["dropped"] += 1
        files["sft.jsonl" if kind == "implement" else "preference.jsonl"] = "".join(lines).encode()
    if holdout:
        files["holdout.txt"] = "".join(stem + "\n" for stem in held).encode()
    return files, counts
