"""Suggest ticket context from the project index."""

import re
from collections import defaultdict
from pathlib import Path

import duckdb

from clutch.tickets import context_path, in_fence


def suggest(conn, stem, fence, context, goal) -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
    files = {row[0] for row in conn.execute("SELECT path FROM files").fetchall()}
    chunks = conn.execute("SELECT path, selector, text FROM chunks").fetchall()
    touches = conn.execute("SELECT ticket, path FROM touches WHERE ticket != ?", [stem]).fetchall()
    by_ticket = defaultdict(set)
    for ticket, path in touches:
        by_ticket[ticket].add(path)
    scores = defaultdict(set)
    shared = defaultdict(lambda: defaultdict(set))
    named_paths = {context_path(entry) for entry in context}
    for ticket, paths in by_ticket.items():
        matched = [entry for entry in fence if any(in_fence(path, [entry]) for path in paths)]
        if not matched:
            continue
        for path in paths:
            if path not in files or path.startswith("tickets/") or in_fence(path, fence) or path in named_paths:
                continue
            scores[path].add(ticket)
            for entry in matched:
                shared[path][entry].add(ticket)
    ranked = sorted(scores, key=lambda path: (-len(scores[path]), path))[:5]
    result_files = []
    for path in ranked:
        entry = min(shared[path], key=lambda item: (-len(shared[path][item]), item))
        result_files.append((path, f"changed with {entry} in {len(scores[path])} past tickets"))
    terms = set(re.findall(r"[a-z0-9_]{4,}", " ".join(re.findall(r"`([^`]*)`", goal)).lower()))
    matches = []
    for path, selector, text in chunks:
        if path not in files or path.startswith(("tickets/", "box:")) or selector in context:
            continue
        found = sorted(term for term in terms if term in text.lower())
        if len(found) >= 2:
            matches.append((selector, found))
    matches.sort(key=lambda item: (-len(item[1]), item[0]))
    return result_files, [(selector, "matches " + ", ".join(found[:5])) for selector, found in matches[:5]]


def hint_block(state_dir: Path, stem, fence, context, text, *, connect=duckdb.connect) -> str:
    try:
        if not text.strip():
            return "none"
        path = state_dir / "index.duckdb"
        if not path.exists():
            return "unavailable: no_index (run clutch index build)"
        conn = connect(str(path), read_only=True)
        try:
            files, sections = suggest(conn, stem, fence, context, text)
            return "\n".join(("- " + " ".join(selector.split()) + "  # " + " ".join(reason.split()))[:300] for selector, reason in [*files, *sections]) or "none"
        finally:
            conn.close()
    except Exception:
        return "unavailable: index_unreadable"


def suggest_for_stem(state_dir, root, stem, *, fs, connect=duckdb.connect):
    from clutch import runner, tickets
    from clutch.tickets import ticket_path

    if not tickets.STEM.fullmatch(stem) or stem in tickets.RESERVED_STEMS:
        raise runner.Refusal("refused: invalid stem", "choose a valid ticket stem", code="invalid_stem")
    path = root / ticket_path(stem)
    try:
        body = fs.read_bytes(path).decode("utf-8")
    except OSError, UnicodeDecodeError:
        raise runner.Refusal("refused: ticket is missing or unreadable UTF-8", "create a readable ticket", code="missing_ticket") from None
    sections, _ = tickets._sections(body, str(path))
    for name in ("Goal / Why", "Scope fence"):
        if not sections.get(name, "").strip():
            raise runner.Refusal(f"refused: missing or blank {name}", f"fill in ## {name}", code="missing_section")
    fence, _ = tickets._bullets(sections["Scope fence"], "Scope fence", str(path))
    entries, _ = tickets._bullets(sections.get("Context", ""), "Context", str(path))
    database = state_dir / "index.duckdb"
    try:
        fs.size(database)
    except FileNotFoundError:
        raise runner.Refusal("no_index", "run clutch index build", code="no_index") from None
    except OSError:
        raise runner.Refusal("index_unreadable", "retry after the running refresh finishes, or run clutch index build if the index lacks a table", code="index_unreadable") from None
    try:
        conn = connect(str(database), read_only=True)
        try:
            files, chunks = suggest(conn, stem, fence, entries, sections["Goal / Why"])
        finally:
            conn.close()
    except duckdb.Error:
        raise runner.Refusal("index_unreadable", "retry after the running refresh finishes, or run clutch index build if the index lacks a table", code="index_unreadable") from None
    return files, chunks
