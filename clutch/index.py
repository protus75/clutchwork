"""Incremental, rebuildable project index."""

import ast
import hashlib
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import duckdb

from clutch import meta
from clutch.box import BOX_DIR, Box, BoxError, parse_record
from clutch.evidence.store import SKIP
from clutch.git import GitError
from clutch.seams import ExecutableNotFound

EMBED_TIMEOUT_S = 60
KINDS = ("box", "roadmap", "decision")
_FLOAT_MAX = 3.4028234663852886e38


class IndexCreator(Protocol):
    def load(self, connection, kind: str) -> list[str]: ...

    def create(self, connection, kind: str) -> list[str]: ...


class _Creator:
    def load(self, connection, kind):
        try:
            connection.execute(f"INSTALL {kind}")
            connection.execute(f"LOAD {kind}")
        except duckdb.Error as exc:
            return [f"{kind} unavailable: {exc}"]
        return []

    def create(self, connection, kind):
        try:
            if kind == "vss":
                connection.execute("SET hnsw_enable_experimental_persistence = true")
                connection.execute("CREATE INDEX IF NOT EXISTS embeddings_hnsw ON embeddings USING HNSW (vec)")
            else:
                connection.execute("PRAGMA create_fts_index('chunks', 'selector', 'text', overwrite=1)")
        except duckdb.Error as exc:
            return [f"{kind} unavailable: {exc}"]
        return []


default_creator = _Creator()


def _exists(conn, table):
    return bool(conn.execute("SELECT count(*) FROM information_schema.tables WHERE table_schema = 'main' AND table_name = ?", [table]).fetchone()[0])


def _extract(path, data):
    kind, purpose, relates, owner = "", "", [], ""
    chunks = []
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return kind, purpose, relates, owner, chunks
    suffix = Path(path).suffix
    try:
        fields, _, _ = meta.parse(text, suffix)
    except meta.Malformed:
        fields = None
    tree = None
    if suffix == ".py":
        try:
            tree = ast.parse(text)
        except SyntaxError:
            pass
        if tree is not None:
            doc = ast.get_docstring(tree)
            if doc:
                purpose = doc.splitlines()[0]
    if fields is not None:
        kind, purpose, relates, owner = (fields[k] for k in ("kind", "purpose", "relates", "owner"))
    if suffix == ".md":
        headings = []
        offset = 0
        fenced = False
        for line in text.splitlines(keepends=True):
            if line.strip().startswith("```"):
                fenced = not fenced
            elif not fenced and (heading := re.match(r"^#{1,6}[ \t]+(.*?)[ \t]*$", line.rstrip("\r\n"))):
                title = re.sub(r"[ \t]+#+[ \t]*$", "", heading.group(1)).strip()
                headings.append((offset, title))
            offset += len(line)
        for i, (start, title) in enumerate(headings):
            chunk = text[start : headings[i + 1][0] if i + 1 < len(headings) else len(text)]
            chunks.append((path, f"{path}#{title}", chunk, len(chunk.split())))
    elif tree is not None:
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                segment = ast.get_source_segment(text, node)
                chunks.append((path, f"{path}::{node.name}", segment, len(segment.split())))
                if isinstance(node, ast.ClassDef):
                    for method in node.body:
                        if isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            segment = ast.get_source_segment(text, method)
                            chunks.append((path, f"{path}::{node.name}.{method.name}", segment, len(segment.split())))
    return kind, purpose, relates, owner, chunks


def _write_entry(conn, path, files_row, chunks, has_embeddings):
    for table in ("files", "chunks") + (("embeddings",) if has_embeddings else ()):
        conn.execute(f"DELETE FROM {table} WHERE path = ?", [path])
    if files_row is not None:
        conn.execute("INSERT INTO files VALUES (?, ?, ?, ?, ?, ?, ?)", files_row)
        for chunk in chunks:
            conn.execute("INSERT INTO chunks VALUES (?, ?, ?, ?)", chunk)


async def _embed_vector(config, root, fs, exec_, env, text, length):
    temp = config.state_dir / "index-embed-input.tmp"
    fs.write(temp, text.encode())
    try:
        try:
            rc, stdout, _ = await exec_.run(config.index.embed, cwd=root, env=env, timeout=EMBED_TIMEOUT_S, stdin_path=temp)
            reason = f"exit {rc}" if rc else None
        except (ExecutableNotFound, TimeoutError, OSError) as exc:
            reason = f"exec {type(exc).__name__}"
    finally:
        fs.remove(temp)
    if reason is None:
        try:
            vector = json.loads(stdout)
        except ValueError, TypeError:
            reason = "not json"
        else:
            if not isinstance(vector, list) or not vector or any(type(x) not in (int, float) or abs(x) > _FLOAT_MAX or not math.isfinite(x) for x in vector):
                reason = "not a vector"
            elif length is not None and len(vector) != length:
                reason = f"length {len(vector)} != {length}"
    return (vector if reason is None else None), reason


async def _embed(conn, config, root, fs, exec_, env):
    exists = _exists(conn, "embeddings")
    length = None
    if exists:
        typename = conn.execute("SELECT data_type FROM information_schema.columns WHERE table_name = 'embeddings' AND column_name = 'vec'").fetchone()[0]
        length = int(re.search(r"\[(\d+)\]$", typename).group(1))
    query = "SELECT path, selector, text FROM chunks"
    if exists:
        query += " WHERE NOT EXISTS (SELECT 1 FROM embeddings e WHERE e.path = chunks.path AND e.selector = chunks.selector)"
    for path, selector, text in conn.execute(query).fetchall():
        vector, reason = await _embed_vector(config, root, fs, exec_, env, text, length)
        if reason:
            conn.execute("DROP TABLE IF EXISTS embeddings")
            return [f"embed_failed: {selector}: {reason}"]
        if length is None:
            length = len(vector)
            conn.execute(f"CREATE TABLE embeddings (path VARCHAR, selector VARCHAR, vec FLOAT[{length}])")
        conn.execute("INSERT INTO embeddings VALUES (?, ?, ?)", [path, selector, vector])
    return []


@dataclass(frozen=True)
class Hit:
    kind: str
    ref: str
    selector: str
    text: str
    score: float


@dataclass(frozen=True)
class Neighbors:
    outcome: str
    mode: str = ""
    hits: tuple[Hit, ...] = ()
    findings: tuple[str, ...] = ()


async def neighbors(config, root, text, *, fs, exec_, env, creator, limit=5, kinds=KINDS, exclude=(), connect=duckdb.connect):
    """Find indexed box messages, roadmap rows and decisions."""
    if not isinstance(text, str):
        error = "text: not a string"
    elif not text.strip():
        error = "text: blank"
    elif len(text) > 8000:
        error = "text: longer than 8000 characters"
    elif type(limit) is not int or not 1 <= limit <= 50:
        error = "limit: not an integer in 1..50"
    elif not isinstance(kinds, (list, tuple, set, frozenset)) or not kinds or any(k not in KINDS for k in kinds) or len(set(kinds)) != len(kinds):
        error = "kinds: not a non-empty collection of distinct members of box, roadmap, decision"
    elif not isinstance(exclude, (list, tuple, set, frozenset)) or len(exclude) > 50 or any(not isinstance(x, str) or not x for x in exclude):
        error = "exclude: not a collection of at most 50 non-empty strings"
    else:
        error = None
    if error:
        return Neighbors("invalid_input", findings=(f"invalid_input: {error}",))
    path = config.state_dir / "index.duckdb"
    try:
        fs.size(path)
    except FileNotFoundError:
        return Neighbors("no_index")
    except OSError as exc:
        return Neighbors("index_unreadable", findings=(f"index_unreadable: {exc}",))
    try:
        conn = connect(str(path), read_only=True)
    except Exception as exc:
        return Neighbors("index_unreadable", findings=(f"index_unreadable: {exc}",))
    try:
        try:
            # roadmap leads to runner and merge, which can import index.
            from clutch import roadmap

            # Check both required tables even if the search has no candidates.
            conn.execute("SELECT path, kind FROM files LIMIT 0")
            conn.execute("SELECT path, selector, text FROM chunks LIMIT 0")
            findings = []
            mode = "fulltext"
            if config.index.embed:
                loaded = creator.load(conn, "vss")
                if loaded:
                    reason = loaded[0]
                elif not _exists(conn, "embeddings"):
                    reason = "embeddings table missing"
                else:
                    typename = conn.execute("SELECT data_type FROM information_schema.columns WHERE table_name = 'embeddings' AND column_name = 'vec'").fetchone()[0]
                    length = int(re.search(r"\[(\d+)\]$", typename).group(1))
                    vector, reason = await _embed_vector(config, root, fs, exec_, env, text.strip(), length)
                if reason:
                    findings.append(f"embed_failed: {reason}")
                else:
                    mode = "embedding"
            if mode == "fulltext":
                loaded = creator.load(conn, "fts")
                if loaded:
                    return Neighbors("fulltext_unavailable", findings=tuple(findings + list(loaded)))
                if not conn.execute("SELECT count(*) FROM information_schema.schemata WHERE schema_name = 'fts_main_chunks'").fetchone()[0]:
                    return Neighbors("fulltext_unavailable", findings=tuple(findings + ["fts unavailable: index missing"]))
                sql = "SELECT c.path, c.selector, c.text, f.kind, fts_main_chunks.match_bm25(c.selector, ?) FROM chunks c JOIN files f ON c.path = f.path"
                params = [text.strip()]
            else:
                sql = (
                    f"SELECT c.path, c.selector, c.text, f.kind, 1 - array_cosine_distance(e.vec, CAST(? AS FLOAT[{length}])) "
                    "FROM chunks c JOIN files f ON c.path = f.path JOIN embeddings e ON c.path = e.path AND c.selector = e.selector"
                )
                params = [vector]
            hits = []
            for path, selector, chunk, kind, score in conn.execute(sql, params).fetchall():
                if kind == "box" and selector == f"{path}#summary" and path.startswith("box:"):
                    hit_kind, ref = "box", path[4:]
                elif path == roadmap.ROADMAP and selector.startswith(f"{path}#row "):
                    hit_kind, ref = "roadmap", selector[len(path) + 1 :]
                elif kind == "decision":
                    hit_kind, ref = "decision", path
                else:
                    continue
                if hit_kind in kinds and ref not in exclude and score is not None and math.isfinite(score):
                    hits.append(Hit(hit_kind, ref, selector, chunk, float(score)))
            hits.sort(key=lambda hit: (-hit.score, hit.selector))
            hits = tuple(hits[:limit])
            return Neighbors("found" if hits else "no_match", mode, hits, tuple(findings))
        except duckdb.Error as exc:
            return Neighbors("index_unreadable", findings=(f"index_unreadable: {exc}",))
    finally:
        conn.close()


@dataclass(frozen=True)
class QueryHit:
    path: str
    kind: str
    selector: str
    purpose: str
    relates: tuple[str, ...]
    owner: str
    score: float


@dataclass(frozen=True)
class QueryResult:
    outcome: str
    mode: str = ""
    hits: tuple[QueryHit, ...] = ()
    findings: tuple[str, ...] = ()


async def query(config, root, text, *, fs, exec_, env, creator, limit=10, connect=duckdb.connect):
    """Search indexed repository chunks without a writer lock."""
    if not isinstance(text, str) or not text.strip() or len(text) > 8000:
        return QueryResult("invalid_input", findings=("invalid_input: text must be non-blank and at most 8000 characters",))
    if type(limit) is not int or not 1 <= limit <= 50:
        return QueryResult("invalid_input", findings=("invalid_input: limit must be an integer in 1..50",))
    path = config.state_dir / "index.duckdb"
    try:
        fs.size(path)
    except FileNotFoundError:
        return QueryResult("no_index")
    except OSError as exc:
        return QueryResult("index_unreadable", findings=(f"index_unreadable: {exc}",))
    try:
        conn = connect(str(path), read_only=True)
    except (OSError, duckdb.Error) as exc:
        return QueryResult("index_unreadable", findings=(f"index_unreadable: {exc}",))
    try:
        try:
            conn.execute("SELECT path, kind, purpose, relates, owner FROM files LIMIT 0")
            conn.execute("SELECT path, selector, text FROM chunks LIMIT 0")
            findings = []
            mode = "fulltext"
            if config.index.embed:
                try:
                    loaded = creator.load(conn, "vss")
                    if loaded:
                        reason = loaded[0]
                    elif not _exists(conn, "embeddings"):
                        reason = "embeddings table missing"
                    else:
                        typename = conn.execute("SELECT data_type FROM information_schema.columns WHERE table_name = 'embeddings' AND column_name = 'vec'").fetchone()[0]
                        length = int(re.search(r"\[(\d+)\]$", typename).group(1))
                        vector, reason = await _embed_vector(config, root, fs, exec_, env, text.strip(), length)
                except Exception as exc:
                    reason = str(exc)
                if reason:
                    findings.append(f"embed_failed: {reason}")
                else:
                    mode = "embedding"
            if mode == "fulltext":
                try:
                    loaded = creator.load(conn, "fts")
                    available = not loaded and conn.execute("SELECT count(*) FROM information_schema.schemata WHERE schema_name = 'fts_main_chunks'").fetchone()[0]
                except (OSError, duckdb.Error) as exc:
                    loaded, available = [f"fts unavailable: {exc}"], False
                if not available:
                    return QueryResult("fulltext_unavailable", findings=tuple(findings + (list(loaded) or ["fts unavailable: index missing"])))
                score = "fts_main_chunks.match_bm25(c.selector, ?)"
                join = ""
                params = [text.strip()]
            else:
                score = f"1 - array_cosine_distance(e.vec, CAST(? AS FLOAT[{length}]))"
                join = " JOIN embeddings e ON c.path = e.path AND c.selector = e.selector"
                params = [vector]
            sql = (
                "SELECT c.path, f.kind, c.selector, f.purpose, f.relates, f.owner, "
                + score
                + " FROM chunks c JOIN files f ON c.path = f.path"
                + join
                + " WHERE NOT c.path LIKE 'box:%' AND NOT c.path LIKE 'tickets/%'"
            )
            hits = []
            for path, kind, selector, purpose, relates, owner, value in conn.execute(sql, params).fetchall():
                if value is None or not math.isfinite(value):
                    continue
                try:
                    parsed = json.loads(relates)
                    parsed = tuple(x for x in parsed if isinstance(x, str)) if isinstance(parsed, list) else ()
                except TypeError, ValueError:
                    parsed = ()
                hits.append(QueryHit(path, kind, selector, purpose, parsed, owner, float(value)))
            hits.sort(key=lambda hit: (-hit.score, hit.selector))
            hits = tuple(hits[:limit])
            return QueryResult("found" if hits else "no_match", mode, hits, tuple(findings))
        except (OSError, duckdb.Error) as exc:
            return QueryResult("index_unreadable", findings=(f"index_unreadable: {exc}",))
    finally:
        conn.close()


async def build(config, root, *, fs, git, exec_, env, store, creator, connect=duckdb.connect):
    """Build the index and return closed-outcome findings."""
    try:
        conn = connect(str(config.state_dir / "index.duckdb"))
    except Exception as exc:
        return [f"db_open_failed: {exc}"]
    try:
        extension_findings = []
        vss = False
        if config.index.embed:
            loaded = creator.load(conn, "vss")
            extension_findings.extend(loaded)
            vss = not loaded
        loaded = creator.load(conn, "fts")
        extension_findings.extend(loaded)
        fts = not loaded
        findings = []
        box_finding = []
        conn.execute("CREATE TABLE IF NOT EXISTS files (path VARCHAR, kind VARCHAR, purpose VARCHAR, relates VARCHAR, owner VARCHAR, hash VARCHAR, size BIGINT)")
        conn.execute("CREATE TABLE IF NOT EXISTS chunks (path VARCHAR, selector VARCHAR, text VARCHAR, tokens BIGINT)")
        conn.execute("CREATE TABLE IF NOT EXISTS touches (ticket VARCHAR, commit_sha VARCHAR, path VARCHAR)")
        conn.execute("CREATE TABLE IF NOT EXISTS calls (key VARCHAR, stem VARCHAR, surface VARCHAR, tree_before VARCHAR, tree_after VARCHAR, changed_paths VARCHAR[])")
        git_available = True
        try:
            paths = await git.ls_files(root)
        except GitError as exc:
            git_available = False
            findings.append(f"git_failed: {exc}")
        else:
            if not config.index.embed:
                conn.execute("DROP TABLE IF EXISTS embeddings")
            paths = sorted(p for p in paths if Path(p).suffix in (".md", ".py") and (not p.startswith("tickets/") or (Path(p).parent == Path("tickets/decisions") and Path(p).suffix == ".md")))
            old = dict(conn.execute("SELECT path, hash FROM files").fetchall())
            has_embeddings = vss and _exists(conn, "embeddings")
            try:
                messages = {f"box:{message.id}": message for message in Box(config.state_dir / BOX_DIR, fs).messages()}
            except BoxError as exc:
                box_finding = [f"box_unreadable: {exc}"]
                messages = {}
            keep = set(paths) | set(messages)
            if box_finding:
                keep |= {path for path in old if path.startswith("box:")}
            for path in sorted(set(old) - keep):
                _write_entry(conn, path, None, [], has_embeddings)
            for path in paths:
                data = fs.read_bytes(root / path)
                digest = hashlib.sha256(data).hexdigest()
                if old.get(path) == digest:
                    continue
                if Path(path).parent == Path("tickets/decisions"):
                    kind, purpose, relates, owner, chunks = "decision", "", [], "", []
                    try:
                        record, body = parse_record(data.decode("utf-8"))
                    except UnicodeDecodeError, BoxError:
                        pass
                    else:
                        purpose = next((line.strip() for line in body.splitlines() if line.strip()), "")
                        if body.strip():
                            chunks.append((path, f"{path}#{record.id}", body, len(body.split())))
                else:
                    kind, purpose, relates, owner, chunks = _extract(path, data)
                    if path == "docs/roadmap.md":
                        # roadmap leads to runner and merge, which can import index.
                        from clutch import roadmap

                        if path != roadmap.ROADMAP:
                            continue
                        try:
                            rows = roadmap.parse(data.decode("utf-8"))
                        except roadmap.Refusal, ValueError, UnicodeDecodeError:
                            pass
                        else:
                            for row in rows:
                                text = f"{row.stem}: {row.content}"
                                chunks.append((path, f"{path}#row {row.number}", text, len(text.split())))
                _write_entry(conn, path, [path, kind, purpose, json.dumps(relates), owner, digest, len(data)], chunks, has_embeddings)
            for path, message in messages.items():
                data = message.summary.encode("utf-8")
                digest = hashlib.sha256(data).hexdigest()
                if old.get(path) == digest:
                    continue
                chunks = [(path, f"{path}#summary", message.summary, len(message.summary.split()))]
                _write_entry(conn, path, [path, "box", message.summary.splitlines()[0].strip(), "[]", message.origin, digest, len(data)], chunks, has_embeddings)
            if vss:
                findings.extend(await _embed(conn, config, root, fs, exec_, env))
        try:
            touches = await git.ticket_touches(root)
        except GitError as exc:
            findings.append(f"git_failed: {exc}")
        else:
            existing = set(conn.execute("SELECT DISTINCT ticket, commit_sha FROM touches").fetchall())
            for ticket, sha, paths in touches:
                if (ticket, sha) not in existing:
                    for path in paths:
                        conn.execute("INSERT INTO touches VALUES (?, ?, ?)", [ticket, sha, path])
                    existing.add((ticket, sha))
        existing_calls = {row[0] for row in conn.execute("SELECT key FROM calls").fetchall()}
        for key in store.call_keys(""):
            if key in existing_calls:
                continue
            try:
                start = store.read_record(key, "start")
                if start is SKIP:
                    continue
                try:
                    end = store.read_record(key, "end")
                except FileNotFoundError:
                    continue
                if end is SKIP:
                    continue
            except Exception:
                findings.append(f"call_unreadable: {key}")
                continue
            conn.execute(
                "INSERT INTO calls VALUES (?, ?, ?, ?, ?, ?)",
                [key, start.stem or "", start.surface, start.repo.tree_before if start.repo else "", end.repo.tree_after if end.repo else "", end.repo.changed_paths if end.repo else []],
            )
        findings.extend(box_finding)
        findings.extend(extension_findings)
        if vss and git_available and _exists(conn, "embeddings"):
            findings.extend(creator.create(conn, "vss"))
        elif fts:
            findings.extend(creator.create(conn, "fts"))
        return findings
    finally:
        conn.close()
