"""Read-only MCP server using the stdio JSON-RPC transport."""

import asyncio
import dataclasses
import json
import os
import re
import sys
import time
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path

import duckdb
from pydantic import BaseModel, ConfigDict, ValidationError

from clutch import ask, context, events, observe, roadmap, runner, stats
from clutch.box import UnknownBoxId
from clutch.config import ConfigError, load_config
from clutch.evidence import views
from clutch.evidence.store import SKIP, CaptureNotFound, CaptureUnreadable, EvidenceStore, size_warning
from clutch.git import Git, GitError
from clutch.journal import Journal, JournalCorruption
from clutch.lockfile import CommitLock
from clutch.providers import child_env
from clutch.seams import LocalFileSystem, SubprocessExec


class Repo(BaseModel):
    model_config = ConfigDict(extra="forbid")
    repo: str | None = None


class Snapshot(Repo):
    all_merged: bool = False


class Status(Repo):
    short: bool = False


class Stats(Repo):
    window: str = "7d"
    tree: bool = False


class Wait(Repo):
    cursor: str | None = None
    timeout_seconds: float = 300.0


class Captures(Repo):
    stem: str
    attempt: int | None = None
    name: str | None = None


class Show(Repo):
    call_key: str


class Suggest(Repo):
    stem: str


class Prompt(Repo):
    kind: str
    stems: list[str] = []
    name: str | None = None


TOOLS = {
    "clutch_snapshot": Snapshot,
    "clutch_status": Status,
    "clutch_stats": Stats,
    "clutch_roadmap_status": Repo,
    "clutch_wait_event": Wait,
    "clutch_evidence_captures": Captures,
    "clutch_evidence_show": Show,
    "clutch_context_suggest": Suggest,
    "clutch_prompt": Prompt,
}


def _json(value):
    if isinstance(value, BaseModel):
        return _json(value.model_dump(by_alias=True))
    if dataclasses.is_dataclass(value):
        return {f.name: _json(getattr(value, f.name)) for f in dataclasses.fields(value)}
    if isinstance(value, dict) or hasattr(value, "items"):
        return {str(k): _json(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json(v) for v in value]
    if value is SKIP:
        return None
    if isinstance(value, Path):
        return str(value)
    return value


def _error(exc):
    if isinstance(exc, runner.Refusal):
        return {"code": exc.code, "message": exc.message, "paved_road": exc.paved_road}
    return {"code": type(exc).__name__, "message": str(exc) or type(exc).__name__, "paved_road": "check the repository and retry"}


class ClutchMCPServer:
    def __init__(self, *, default_cwd=None, config_path=None, env=None, clock=None, sleep=time.sleep, monotonic=time.monotonic, exec_factory=SubprocessExec, git_factory=Git, connect=duckdb.connect):
        self.cwd = Path(default_cwd or Path.cwd()).resolve()
        self.config_path = config_path
        self.env = dict(os.environ if env is None else env)
        self.clock = clock or (lambda: datetime.now(UTC))
        self.sleep, self.monotonic = sleep, monotonic
        self.exec_factory, self.git_factory, self.connect = exec_factory, git_factory, connect

    def checkout(self, repo):
        if repo is not None and not repo.strip():
            raise runner.Refusal("blank repo", "supply a checkout containing tickets/", code="invalid_repo")
        root = Path(repo).resolve() if repo is not None else self.cwd
        if not root.is_dir() or not (root / "tickets").is_dir():
            raise runner.Refusal("repo is not a checkout containing tickets/", "supply a checkout containing tickets/", code="invalid_repo")
        path = self.config_path if root == self.cwd else None
        cfg = load_config(path, cwd=root)
        fs = LocalFileSystem()
        exec_ = self.exec_factory()
        git = self.git_factory(exec_, env={**child_env(self.env, cfg), "GIT_OPTIONAL_LOCKS": "0"}, timeout=30.0, commit_lock=CommitLock(cfg.state_dir, clock=self.clock, sleep=asyncio.sleep))
        checkout = runner.Checkout(root, cfg, self.env, exec_, git, Journal(cfg.state_dir, self.clock), fs, self.clock)
        ctx = observe.Context(root, cfg.state_dir, (path or root / "config.yaml"), exec_, git, {**child_env(self.env, cfg), "GIT_OPTIONAL_LOCKS": "0"})
        return checkout, ctx

    def prompt(self, checkout, ctx, kind, stems, name=None):
        def running():
            last = observe.last_bodies(observe.as_events(observe.journal(checkout.config.state_dir)))
            return observe.running_stems(checkout.config.state_dir, last)

        def drafts():
            return [row["stem"] for row in observe.snapshot(ctx)["rows"] if row["draft"]]

        return ask.resolve_prompt(kind, stems, name=name, config=checkout.config, repo=checkout.repo, running_stems=running, draft_stems=drafts)

    def call_tool(self, name, args):
        checkout, ctx = self.checkout(args.repo)
        cfg, fs = checkout.config, checkout.fs
        store = EvidenceStore(cfg.state_dir, fs, fs.read_bytes, fs.size, lambda text: text)
        if name == "clutch_snapshot":
            value = observe.snapshot(ctx, merged_limit=None if args.all_merged else cfg.snapshot_merged_limit)
        elif name == "clutch_status":
            from clutch.__main__ import _status
            from clutch.status import render

            projection = asyncio.run(_status(checkout))
            value = _json(projection)
            if args.short:
                value.pop("scorecard", None)
            value.update(version=version("clutchwork"), evidence_warning=size_warning(store, cfg.evidence.warn_gb))
            return value, render(projection, short=args.short)
        elif name == "clutch_stats":
            history, now = checkout.journal.read(), self.clock()
            try:
                stats.window_start(history, now, args.window)
            except ValueError as exc:
                raise runner.Refusal(str(exc), "use <N>h, <N>d, or <N>t", code="invalid_window") from None
            result = asyncio.run(stats.collect_stats(checkout, history, now, args.window))
            value = {"window": args.window, "tree": stats.stats_tree(result)} if args.tree else result
        elif name == "clutch_roadmap_status":
            value = {"lines": asyncio.run(roadmap.status(checkout))}
        elif name == "clutch_wait_event":
            try:
                cursor, lines, timed_out = events.wait_once(cfg.state_dir, cursor=args.cursor, timeout=args.timeout_seconds, sleep=self.sleep, clock=self.monotonic)
            except ValueError as exc:
                raise runner.Refusal(str(exc), "supply a valid cursor and nonnegative timeout", code="invalid_cursor_or_timeout") from None
            value = {"cursor": cursor, "events": lines, "timed_out": timed_out}
        elif name == "clutch_evidence_captures":
            try:
                if args.name is not None:
                    value = {"capture": store.get_capture(args.stem, args.attempt, args.name).decode("utf-8", errors="replace")}
                else:
                    value = {"captures": store.captures(args.stem, args.attempt)}
            except (ValueError, CaptureNotFound, CaptureUnreadable, OSError) as exc:
                raise runner.Refusal(str(exc) or "capture unavailable", "choose an existing capture and attempt", code="capture_error") from None
        elif name == "clutch_evidence_show":
            try:
                start = store.read_record(args.call_key, "start")
                try:
                    end = store.read_record(args.call_key, "end")
                except FileNotFoundError:
                    end = None
                normalized, _ = store.read_normalized(args.call_key)
                value = {"start": start, "end": end, "normalized": normalized, "lines": views.show_lines(start, end, normalized)}
            except (ValueError, KeyError, OSError) as exc:
                raise runner.Refusal(str(exc) or "evidence unavailable", "choose a readable evidence call", code="evidence_error") from None
        elif name == "clutch_context_suggest":
            files, chunks = context.suggest_for_stem(cfg.state_dir, checkout.repo, args.stem, fs=fs, connect=self.connect)
            value = {"stem": args.stem, "files": files, "chunks": chunks}
        else:
            text, catalog = self.prompt(checkout, ctx, args.kind, args.stems, args.name)
            value = catalog if catalog is not None else {"text": text}
            return value, text or json.dumps(value)
        value = _json(value)
        return value, json.dumps(value)

    def dispatch(self, method, params):
        if method == "initialize":
            requested = params.get("protocolVersion")
            return {
                "protocolVersion": requested if requested in {"2025-03-26", "2024-11-05"} else "2025-03-26",
                "capabilities": {"tools": {"listChanged": False}, "prompts": {"listChanged": False}},
                "serverInfo": {"name": "clutchwork", "version": version("clutchwork")},
            }
        if method == "ping":
            return {}
        if method == "tools/list":
            return {"tools": [{"name": name, "description": name.replace("_", " "), "inputSchema": model.model_json_schema()} for name, model in TOOLS.items()]}
        if method == "prompts/list":
            result = []
            for kind in ask.KINDS:
                arguments = [{"name": "repo", "required": False}]
                if ask.TAKES[kind] != "none":
                    arguments.append({"name": "ids" if kind == "box" else "stem", "required": True})
                result.append({"name": kind, "description": ask.DESCRIPTIONS[kind], "arguments": arguments})
            return {"prompts": result}
        if method == "tools/call":
            name = params.get("name")
            if not isinstance(name, str) or name not in TOOLS:
                raise InvalidParams("unknown tool")
            try:
                args = TOOLS[name].model_validate(params.get("arguments", {}))
            except ValidationError as exc:
                raise InvalidParams(str(exc)) from None
            try:
                value, text = self.call_tool(name, args)
                return {"content": [{"type": "text", "text": text or "(empty)"}], "structuredContent": _json(value)}
            except (runner.Refusal, ConfigError, JournalCorruption, GitError, UnknownBoxId, ValueError) as exc:
                value = _error(exc)
                return {"isError": True, "content": [{"type": "text", "text": value["message"]}], "structuredContent": value}
        if method == "prompts/get":
            kind = params.get("name")
            if not isinstance(kind, str) or kind not in ask.KINDS:
                raise InvalidParams("unknown prompt")
            args = params.get("arguments", {})
            if not isinstance(args, dict) or set(args) - {"repo", "stem" if ask.TAKES[kind] == "stem" else "ids" if kind == "box" else "repo"}:
                raise InvalidParams("invalid prompt arguments")
            takes = ask.TAKES[kind]
            arg = args.get("stem" if takes == "stem" else "ids") if takes != "none" else None
            if takes != "none" and not arg:
                raise InvalidParams("missing prompt argument")
            if takes == "stem" and not isinstance(arg, str):
                raise InvalidParams("invalid stem")
            if takes == "box":
                if isinstance(arg, str):
                    stems = [s for s in re.split(r"[,\s]+", arg) if s]
                elif isinstance(arg, list) and all(isinstance(s, str) for s in arg):
                    stems = arg
                else:
                    raise InvalidParams("invalid ids")
            else:
                stems = [arg] if takes == "stem" else []
            if args.get("repo") is not None and not isinstance(args["repo"], str):
                raise InvalidParams("invalid repo")
            try:
                checkout, ctx = self.checkout(args.get("repo"))
                text, _ = self.prompt(checkout, ctx, kind, stems)
                return {"description": ask.DESCRIPTIONS[kind], "messages": [{"role": "user", "content": {"type": "text", "text": text}}]}
            except (runner.Refusal, ConfigError, JournalCorruption, GitError, UnknownBoxId) as exc:
                raise DomainError(_error(exc)) from None
        raise UnknownMethod(method)


class InvalidParams(Exception):
    pass


class UnknownMethod(Exception):
    pass


class DomainError(Exception):
    pass


def serve_stdio(*, stdin=None, stdout=None, **kwargs):
    stdin = stdin if stdin is not None else sys.stdin
    stdout = stdout if stdout is not None else sys.stdout
    server = ClutchMCPServer(**kwargs)
    for line in stdin:
        if not line.strip():
            continue
        id_ = None
        try:
            try:
                request = json.loads(line)
            except json.JSONDecodeError:
                raise RPCError(-32700, "Parse error") from None
            if not isinstance(request, dict) or request.get("jsonrpc") != "2.0" or not isinstance(request.get("method"), str):
                raise RPCError(-32600, "Invalid Request")
            id_ = request.get("id")
            if "id" not in request:
                continue
            try:
                if not isinstance(request.get("params", {}), dict):
                    raise InvalidParams("params must be an object")
                result = server.dispatch(request["method"], request.get("params", {}))
            except InvalidParams as exc:
                raise RPCError(-32602, str(exc)) from None
            except UnknownMethod:
                raise RPCError(-32601, "Method not found") from None
            except DomainError as exc:
                raise RPCError(-32000, "Domain refusal", exc.args[0]) from None
            response = {"jsonrpc": "2.0", "id": id_, "result": result}
        except RPCError as exc:
            error = {"code": exc.code, "message": str(exc)}
            if exc.data is not None:
                error["data"] = exc.data
            response = {"jsonrpc": "2.0", "id": id_, "error": error}
        except Exception:
            response = {"jsonrpc": "2.0", "id": id_, "error": {"code": -32603, "message": "Internal error"}}
        stdout.write(json.dumps(response) + "\n")
        stdout.flush()


class RPCError(Exception):
    def __init__(self, code, message, data=None):
        super().__init__(message)
        self.code, self.data = code, data
