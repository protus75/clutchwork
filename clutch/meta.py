"""Metadata blocks for tracked Markdown and Python files."""

import ast
import hashlib
import posixpath
import re
from pathlib import Path

import yaml

KEYS = ("schema", "kind", "purpose", "relates", "owner", "verified", "hash")
KINDS = {"doc", "guide", "spec", "test", "fixture", "plan"}


class Malformed(ValueError):
    """A metadata block does not follow the closed schema."""


def _offset(text, suffix):
    if suffix == ".md":
        if text.startswith("---\n"):
            end = text.find("\n---\n", 4)
            if end >= 0:
                return end + 5
        return 0
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return 0
    if tree.body and isinstance(tree.body[0], ast.Expr) and isinstance(tree.body[0].value, ast.Constant) and isinstance(tree.body[0].value.value, str):
        return sum(len(line) for line in text.splitlines(keepends=True)[: tree.body[0].end_lineno])
    return 0


def parse(text, suffix):
    """Return (fields, body, insertion offset), or (None, text, offset)."""
    offset = _offset(text, suffix)
    tail = text[offset:]
    if suffix == ".md":
        if not tail.startswith("<!-- clutch:meta\n"):
            return None, text, offset
        end = tail.find("-->\n")
        if end < 0:
            raise Malformed()
        lines = tail[len("<!-- clutch:meta\n") : end].splitlines()
        size = end + 4
    else:
        if not tail.startswith("# clutch:meta\n"):
            return None, text, offset
        lines = tail.splitlines(keepends=True)
        if len(lines) < 8 or any(not line.startswith("# ") for line in lines[1:8]):
            raise Malformed()
        size = sum(map(len, lines[:8]))
        lines = [line[2:].rstrip("\r\n") for line in lines[1:8]]
    if len(lines) != len(KEYS):
        raise Malformed()
    fields = {}
    for line in lines:
        key, sep, value = line.partition(":")
        if not sep or key not in KEYS or key in fields:
            raise Malformed()
        fields[key] = value.strip()
    if set(fields) != set(KEYS) or fields["schema"] != "clutch.meta/1.0" or fields["kind"] not in KINDS:
        raise Malformed()
    try:
        relates = yaml.safe_load(fields["relates"])
    except yaml.YAMLError as exc:
        raise Malformed() from exc
    if not isinstance(relates, list) or any(not isinstance(p, str) for p in relates):
        raise Malformed()
    fields["relates"] = relates
    return fields, text[:offset] + tail[size:], offset


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


def _relates(text, path, tracked):
    found = set()

    def module(name):
        base = name.replace(".", "/")
        return next((p for p in (base + ".py", base + "/__init__.py") if p in tracked), None)

    if path.endswith(".py"):
        try:
            tree = ast.parse(text)
        except SyntaxError:
            return []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                found.update(p for alias in node.names if (p := module(alias.name)))
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                for alias in node.names:
                    p = module(node.module + "." + alias.name) or module(node.module)
                    if p:
                        found.add(p)
    else:
        links = re.findall(r"\]\(([^)#]+)(?:#[^)]*)?\)|([\w./-]+)::[\w.]+", text)
        for link, selector in links:
            target = posixpath.normpath(posixpath.join(posixpath.dirname(path), link)) if link else selector
            if target in tracked:
                found.add(target)
    return sorted(found - {path})


def _render(fields, suffix):
    values = {**fields, "relates": "[" + ", ".join(fields["relates"]) + "]"}
    lines = [f"{key}: {values[key]}".rstrip() for key in KEYS]
    if suffix == ".md":
        return "<!-- clutch:meta\n" + "\n".join(lines) + "\n-->\n"
    return "# clutch:meta\n" + "".join(f"# {line}\n" for line in lines)


def _files(config, tracked, paths):
    for path in sorted(tracked):
        if not path.endswith((".md", ".py")):
            continue
        for entry in config.meta.paths:
            root = entry.root.rstrip("/")
            if path.startswith(root + "/") and (not paths or any(path == p.rstrip("/") or path.startswith(p.rstrip("/") + "/") for p in paths)):
                parts = path.split("/")
                kind = "fixture" if root == "tests" and ({"fixtures", "harness"} & set(parts[:-1])) else entry.kind
                yield path, kind
                break


def generated(fields, body, path, kind, tracked, sha):
    """Compute deterministic fields without writing the file."""
    new = fields is None
    fields = dict(fields) if fields is not None else dict(schema="clutch.meta/1.0", kind=kind, purpose="", relates=[], owner="", verified="", hash="")
    fields["relates"] = [p for p in fields["relates"] if p in tracked]
    generated_relates = not fields["relates"]
    if generated_relates:
        fields["relates"] = _relates(body, path, set(tracked))
    if generated_relates and path.endswith(".py"):
        # Use the composed block's bounded list when deriving the default owner.
        _, fields = compose(fields, body, _offset(body, ".py"), ".py", trim=True)
    if not fields["owner"]:
        counts = {p: fields["relates"].count(p) for p in fields["relates"]}
        fields["owner"] = next((p for p, n in counts.items() if n > len(fields["relates"]) / 2), "engine")
    current_hash = digest(body)
    if new or fields["hash"] != current_hash:
        fields["verified"] = sha[:8]
        fields["hash"] = current_hash
    return fields, generated_relates


def compose(fields, body, offset, suffix, *, trim=False):
    """Compose a block using the same generated-relates limit for both verbs."""
    fields = dict(fields)
    fields["relates"] = list(fields["relates"])
    if trim and suffix == ".py":
        while len("# relates: [" + ", ".join(fields["relates"]) + "]") > 160:
            fields["relates"].pop()
    return body[:offset] + _render(fields, suffix) + body[offset:], fields


def refresh(config, root, fs, tracked, sha, paths=()):
    changed, malformed = [], []
    for path, kind in _files(config, tracked, paths):
        text = fs.read_bytes(root / path).decode()
        suffix = Path(path).suffix
        try:
            fields, body, offset = parse(text, suffix)
        except Malformed:
            malformed.append(path)
            continue
        fields, generated_relates = generated(fields, body, path, kind, tracked, sha)
        result, _ = compose(fields, body, offset, suffix, trim=generated_relates)
        if result != text:
            fs.write(root / path, result.encode())
            changed.append(path)
    return changed, malformed


def check(config, root, fs, tracked, sha, paths=()):
    findings = []
    for path, _ in _files(config, tracked, paths):
        text = fs.read_bytes(root / path).decode()
        try:
            fields, body, _ = parse(text, Path(path).suffix)
        except Malformed:
            findings.append((path, "malformed"))
            continue
        if fields is None:
            findings.append((path, "missing"))
        else:
            if not fields["purpose"]:
                findings.append((path, "empty_purpose"))
            if fields["hash"] != digest(body):
                findings.append((path, "drifted"))
    return findings
