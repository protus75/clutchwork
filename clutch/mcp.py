"""MCP server using the stdio JSON-RPC transport."""

import asyncio
import concurrent.futures
import dataclasses
import json
import os
import re
import sys
import threading
import time
from contextlib import redirect_stdout
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path
from typing import Literal
from urllib.parse import unquote, urlparse

import duckdb
import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from clutch import ask, box, context, events, hostfiles, index, observe, roadmap, runner, seams, serve, stats, tickets
from clutch.box import UnknownBoxId
from clutch.config import ConfigError, load_config, load_config_text
from clutch.evidence import views
from clutch.evidence.store import SKIP, CaptureNotFound, CaptureUnreadable, EvidenceStore, size_warning
from clutch.git import Git, GitError
from clutch.journal import Journal, JournalCorruption
from clutch.lockfile import CommitLock, CommitLockTimeout, LockHeld
from clutch.providers import ProviderSetupError, child_env
from clutch.seams import ExecutableNotFound, LocalFileSystem, SubprocessExec

DASHBOARD_URI = "ui://clutch/dashboard.html"
MCP_APP_MIME = "text/html;profile=mcp-app"
DEFAULT_DASHBOARD_HTML = Path(__file__).parent / "ui" / "dashboard.html"


def default_last_repo_path(env=None) -> Path:
    values = os.environ if env is None else env
    base = Path(values["XDG_CONFIG_HOME"]) if values.get("XDG_CONFIG_HOME") else Path.home() / ".config"
    return base / "clutch" / "last-repo"


def record_active_repo_from_hook(stdin, *, last_repo_path=None, env=None, fs=None) -> dict[str, object]:
    try:
        data = json.load(stdin)
        if not isinstance(data, dict):
            return {}
        paths = data.get("workspacePaths")
        candidates = [p for p in paths if isinstance(p, str)] if isinstance(paths, list) else []
        if isinstance(data.get("cwd"), str):
            candidates.append(data["cwd"])
        for candidate in candidates:
            if not candidate.strip():
                continue
            root = Path(candidate).resolve()
            if root.is_dir() and (root / "tickets").is_dir():
                path = last_repo_path if last_repo_path is not None else default_last_repo_path(env)
                try:
                    remembered = path.read_text(encoding="utf-8").strip()
                except OSError, UnicodeError:
                    remembered = ""
                if remembered != str(root):
                    (fs if fs is not None else LocalFileSystem()).write(path, f"{root}\n".encode())
                break
    except OSError, ValueError, TypeError, UnicodeError, RecursionError:
        pass
    return {}


class Repo(BaseModel):
    model_config = ConfigDict(extra="forbid")
    repo: str | None = None


class Dashboard(Repo):
    tab: Literal["tickets", "steps", "box", "stats", "help"] = "tickets"


class UiState(Repo):
    action: Literal["get", "set"]
    state: dict[str, object] | None = None


class AppConfig(Repo):
    action: Literal["get", "set"]
    updates: dict[str, object] | None = None


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


class IndexQuery(Repo):
    text: str
    limit: int = 10


class Prompt(Repo):
    kind: str
    stems: list[str] = []
    name: str | None = None


class TicketNew(Repo):
    stem: str
    kind: tickets.Kind = "feature"
    evidence: list[str] = []
    reference: list[str] = []
    inputs: list[str] = []


class TicketLint(Repo):
    stems: list[str] = []


class TicketOrder(Suggest):
    priority: tickets.Priority | None = None
    runs_before: list[str] | None = None


class TicketReject(Suggest):
    reason: str | None = None


class BoxSuggest(Repo):
    summary: str


class BoxTriage(Repo):
    ids: list[str] = []


class BoxDismiss(Repo):
    ids: list[str] = Field(min_length=1)


class EngineStart(Repo):
    mode: Literal["drain", "serve"]


class EngineControl(Repo):
    action: Literal["ping", "pause", "resume", "stop", "kill"]


@dataclasses.dataclass(frozen=True)
class ToolSpec:
    model: type[BaseModel]
    visibility: tuple[Literal["model", "app"], ...]
    blocking: Literal["fast", "wait", "submit_only"] = "fast"


HOST_PROMPT_DESCRIPTION = "Render a host-defined prompt from prompts_dir."


TOOLS: dict[str, ToolSpec] = {
    "clutch_open_dashboard": ToolSpec(Dashboard, ("model", "app")),
    "clutch_app_ui_state": ToolSpec(UiState, ("app",)),
    "clutch_app_config": ToolSpec(AppConfig, ("app",)),
    "clutch_app_snapshot": ToolSpec(Snapshot, ("app",)),
    "clutch_app_stats": ToolSpec(Stats, ("app",)),
    "clutch_snapshot": ToolSpec(Snapshot, ("model", "app")),
    "clutch_status": ToolSpec(Status, ("model", "app")),
    "clutch_stats": ToolSpec(Stats, ("model", "app")),
    "clutch_roadmap_status": ToolSpec(Repo, ("model", "app")),
    "clutch_wait_event": ToolSpec(Wait, ("model",), "wait"),
    "clutch_evidence_captures": ToolSpec(Captures, ("model", "app")),
    "clutch_evidence_show": ToolSpec(Show, ("model", "app")),
    "clutch_context_suggest": ToolSpec(Suggest, ("model", "app")),
    "clutch_index_query": ToolSpec(IndexQuery, ("model", "app")),
    "clutch_prompt": ToolSpec(Prompt, ("model", "app")),
    "clutch_ticket_new": ToolSpec(TicketNew, ("model", "app")),
    "clutch_ticket_lint": ToolSpec(TicketLint, ("model", "app")),
    "clutch_ticket_order": ToolSpec(TicketOrder, ("model", "app")),
    "clutch_ticket_confirm": ToolSpec(Suggest, ("model", "app")),
    "clutch_ticket_reject": ToolSpec(TicketReject, ("model", "app")),
    "clutch_app_ticket_confirm": ToolSpec(Suggest, ("app",)),
    "clutch_app_ticket_reject": ToolSpec(TicketReject, ("app",)),
    "clutch_box_suggest": ToolSpec(BoxSuggest, ("model", "app")),
    "clutch_box_triage": ToolSpec(BoxTriage, ("model", "app"), "submit_only"),
    "clutch_box_dismiss": ToolSpec(BoxDismiss, ("model", "app")),
    "clutch_engine_start": ToolSpec(EngineStart, ("model", "app")),
    "clutch_engine_control": ToolSpec(EngineControl, ("model", "app")),
    "clutch_engine_retro": ToolSpec(Repo, ("model", "app"), "submit_only"),
}


async def _submit_only(checkout, verb, *, ids=None):
    try:
        async with runner._locked(checkout.config.state_dir, verb, instance_id=await checkout.git.describe(checkout.repo), clock=checkout.clock):
            pass
    except LockHeld as exc:
        request = await runner.submit_engine(checkout, exc, verb, **({"ids": ids} if verb == "triage" else {}))
        return {"submitted": True, "request_id": request.request_id}
    raise runner.Refusal("engine is not running", "start the engine with clutch_engine_start or run clutch box triage / clutch engine retro from the CLI", code="engine_not_running")


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
    if isinstance(exc, LockHeld):
        return {"code": "lock_held", "message": str(exc), "paved_road": "wait for the current writer to finish, then retry"}
    if isinstance(exc, runner.Refusal):
        return {"code": exc.code, "message": exc.message, "paved_road": exc.paved_road}
    return {"code": type(exc).__name__, "message": str(exc) or type(exc).__name__, "paved_road": "check the repository and retry"}


def _recent_repos(value):
    result = []
    if isinstance(value, list):
        for item in value:
            if isinstance(item, str):
                try:
                    path = Path(item).resolve()
                    if path.is_dir() and (path / "tickets").is_dir() and str(path) not in result:
                        result.append(str(path))
                        if len(result) == 10:
                            break
                except OSError, ValueError, RuntimeError:
                    pass
    return result


def _read_ui_state(path):
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except OSError, ValueError, UnicodeError, TypeError:
        return {}


def _validate_tool(params):
    name = params.get("name")
    if not isinstance(name, str) or name not in TOOLS:
        raise InvalidParams("unknown tool")
    try:
        return TOOLS[name].model.model_validate(params.get("arguments", {}))
    except ValidationError as exc:
        if name == "clutch_app_config" and isinstance(params.get("arguments"), dict) and "updates" in params["arguments"]:
            return None
        raise InvalidParams(str(exc)) from None


class ClutchMCPServer:
    def __init__(
        self,
        *,
        default_cwd=None,
        ui_html_path: Path | None = None,
        last_repo_path: Path | None = None,
        ui_state_path: Path | None = None,
        config_path=None,
        env=None,
        clock=None,
        sleep=time.sleep,
        monotonic=time.monotonic,
        exec_factory=SubprocessExec,
        git_factory=Git,
        connect=duckdb.connect,
        creator=index.default_creator,
        spawn=seams.spawn_detached,
    ):
        self.ui_html_path = ui_html_path if ui_html_path is not None else DEFAULT_DASHBOARD_HTML
        self.creator = creator
        self.spawn = spawn
        self.cwd = Path(default_cwd or Path.cwd()).resolve()
        self.config_path = config_path
        self.env = dict(os.environ if env is None else env)
        self.last_repo_path = last_repo_path if last_repo_path is not None else default_last_repo_path(self.env)
        self.ui_state_path = (
            ui_state_path if ui_state_path is not None else (Path(self.env["XDG_CONFIG_HOME"]) if self.env.get("XDG_CONFIG_HOME") else Path.home() / ".config") / "clutch" / "dashboard-state.json"
        )
        self.client_supports_roots = False
        self.roots: list[Path] = []
        self.clock = clock or (lambda: datetime.now(UTC))
        self.sleep, self.monotonic = sleep, monotonic
        self.exec_factory, self.git_factory, self.connect = exec_factory, git_factory, connect

    def default_repo(self):
        try:
            remembered = self.last_repo_path.read_text(encoding="utf-8").strip()
        except OSError, UnicodeError:
            remembered = ""
        for root in [*self.roots, Path(remembered) if remembered else None, self.cwd]:
            if root is not None and root.is_dir() and (root / "tickets").is_dir():
                return root
        return None

    def checkout(self, repo):
        if repo is not None and not repo.strip():
            raise runner.Refusal("blank repo", "supply a checkout containing tickets/", code="invalid_repo")
        root = Path(repo).resolve() if repo is not None else self.default_repo()
        if root is None or not root.is_dir() or not (root / "tickets").is_dir():
            raise runner.Refusal("repo is not a checkout containing tickets/", "supply a checkout containing tickets/", code="invalid_repo")
        path = self.config_path if root == self.cwd else None
        cfg = load_config(path, cwd=root)
        fs = LocalFileSystem()
        exec_ = self.exec_factory()
        git = self.git_factory(exec_, env={**child_env(self.env, cfg), "GIT_OPTIONAL_LOCKS": "0"}, timeout=30.0, commit_lock=CommitLock(cfg.state_dir, clock=self.clock, sleep=asyncio.sleep))
        checkout = runner.Checkout(root, cfg, self.env, exec_, git, Journal(cfg.state_dir, self.clock), fs, self.clock)
        ctx = observe.Context(root, cfg.state_dir, (path or root / "config.yaml"), exec_, git, {**child_env(self.env, cfg), "GIT_OPTIONAL_LOCKS": "0"})
        try:
            self.last_repo_path.parent.mkdir(parents=True, exist_ok=True)
            self.last_repo_path.write_text(str(root), encoding="utf-8")
        except OSError:
            pass
        state = _read_ui_state(self.ui_state_path)
        recent = state.get("recentRepos")
        state["recentRepos"] = _recent_repos([str(root.resolve()), *(recent if isinstance(recent, list) else [])])
        try:
            self.ui_state_path.parent.mkdir(parents=True, exist_ok=True)
            self.ui_state_path.write_text(json.dumps(state), encoding="utf-8")
        except OSError:
            pass
        return checkout, ctx

    def prompt(self, checkout, ctx, kind, stems, name=None):
        def running():
            last = observe.last_bodies(observe.as_events(observe.journal(checkout.config.state_dir)))
            return observe.running_stems(checkout.config.state_dir, last)

        def drafts():
            return [row["stem"] for row in observe.snapshot(ctx)["rows"] if row["draft"]]

        return ask.resolve_prompt(kind, stems, name=name, config=checkout.config, repo=checkout.repo, running_stems=running, draft_stems=drafts)

    def call_tool(self, name, args):
        if name == "clutch_app_ui_state":
            keys = ["details", "steps", "tickets", "box", "stats", "settings", "help"]
            state = {"order": keys[:], "open": {k: k in keys[:3] for k in keys}, "heights": {}, "refreshSeconds": 15, "statsWindow": "7d", "playAction": "drain"}

            def merge(incoming):
                if not isinstance(incoming, dict):
                    return
                order = incoming.get("order")
                if isinstance(order, list) and len(order) == len(keys) and all(isinstance(x, str) for x in order) and set(order) == set(keys):
                    state["order"] = order
                for field in ("open", "heights"):
                    values = incoming.get(field)
                    if isinstance(values, dict):
                        for key, value in values.items():
                            if key in keys and (isinstance(value, bool) if field == "open" else isinstance(value, (int, float)) and not isinstance(value, bool) and value >= 0):
                                state[field][key] = value
                value = incoming.get("refreshSeconds")
                if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
                    state["refreshSeconds"] = value
                for field, allowed in (("statsWindow", ("24h", "7d", "30d", "20t")), ("playAction", ("drain", "serve"))):
                    if incoming.get(field) in allowed:
                        state[field] = incoming[field]

            incoming = _read_ui_state(self.ui_state_path)
            merge(incoming)
            state["recentRepos"] = _recent_repos(incoming.get("recentRepos"))
            saved = [key for key, value in incoming.get("open", {}).items() if key in keys and isinstance(value, bool)] if isinstance(incoming.get("open"), dict) else []
            if args.action == "set":
                merge(args.state)
                try:
                    self.ui_state_path.parent.mkdir(parents=True, exist_ok=True)
                    self.ui_state_path.write_text(json.dumps(state), encoding="utf-8")
                except OSError:
                    pass
            result = {**state, "saved": saved}
            return result, json.dumps(result)
        if name == "clutch_open_dashboard" and args.repo is None and self.default_repo() is None:
            value = {"repo": None, "tab": args.tab, "ready": False, "version": version("clutchwork"), "message": "Supply a ClutchWork checkout path to load the dashboard."}
            return value, value["message"]
        checkout, ctx = self.checkout(args.repo)
        cfg, fs = checkout.config, checkout.fs
        store = EvidenceStore(cfg.state_dir, fs, fs.read_bytes, fs.size, lambda text: text)
        if name == "clutch_app_config":

            def selected(config):
                retro = config.retro
                return {
                    "retro": {
                        "enabled": retro.enabled,
                        "merges": retro.merges.model_dump(include={"enabled", "every"}),
                        "settled": retro.settled.model_dump(include={"enabled", "every"}),
                        "spikes": retro.spikes.model_dump(include={"enabled", "count"}),
                    },
                    "scheduler": {"parallel": config.scheduler.parallel.model_dump(include={"enabled", "max_runs"})},
                }

            if args.action == "set":
                allowed = {
                    "retro": {"enabled": None, "merges": {"enabled": None, "every": None}, "settled": {"enabled": None, "every": None}, "spikes": {"enabled": None, "count": None}},
                    "scheduler": {"parallel": {"enabled": None, "max_runs": None}},
                }

                def apply(target, updates, schema):
                    if not isinstance(updates, dict) or not isinstance(target, dict):
                        raise ValueError("updates must be mappings")
                    for key, value in updates.items():
                        if key not in schema:
                            raise ValueError(f"disallowed config key: {key}")
                        if schema[key] is None:
                            target[key] = value
                        else:
                            apply(target.setdefault(key, {}), value, schema[key])

                try:
                    raw = yaml.safe_load(ctx.config.read_text())
                    apply(raw, args.updates, allowed)
                    text = yaml.safe_dump(raw, sort_keys=False)
                    cfg = load_config_text(text, path=ctx.config, cwd=checkout.repo)
                except (ValueError, TypeError, yaml.YAMLError, ConfigError) as exc:
                    raise runner.Refusal(str(exc), "supply valid retro or scheduler.parallel settings", code="invalid_config") from None
                fs.write(ctx.config, text.encode())
            value = selected(cfg)
            return value, json.dumps(value)
        elif name == "clutch_open_dashboard":
            snapshot = observe.snapshot(ctx, merged_limit=cfg.snapshot_merged_limit)
            value = {
                "repo": str(checkout.repo),
                "tab": args.tab,
                "ready": True,
                **{key: snapshot[key] for key in ("counts", "engine", "runningStem", "blockedCount")},
                "pendingBox": snapshot["boxCounts"]["pending"],
                "version": version("clutchwork"),
            }
            return value, f"ClutchWork dashboard ready for {checkout.repo}."
        if name in {"clutch_snapshot", "clutch_app_snapshot"}:
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
        elif name in {"clutch_stats", "clutch_app_stats"}:
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
        elif name == "clutch_index_query":
            value = asyncio.run(
                index.query(cfg, checkout.repo, args.text, fs=fs, exec_=checkout.exec_, env=child_env(self.env, cfg, serving=None), creator=self.creator, limit=args.limit, connect=self.connect)
            )
            if value.outcome not in ("found", "no_match"):
                remedies = {
                    "invalid_input": "provide non-blank text and a limit from 1 to 50",
                    "no_index": "run clutch index build",
                    "index_unreadable": "retry after refresh or run clutch index build",
                    "fulltext_unavailable": "run clutch index build with full-text search available",
                }
                raise runner.Refusal(value.findings[-1] if value.findings else value.outcome, remedies[value.outcome], code=value.outcome)
        elif name == "clutch_ticket_new":
            rel, guide, findings = tickets.new_ticket(checkout.repo, args.stem, args.kind, evidence=args.evidence, reference=args.reference, inputs=args.inputs, fs=fs)
            value = {"stem": args.stem, "path": rel, "guide": guide, "findings": findings}
        elif name == "clutch_ticket_lint":
            result = asyncio.run(tickets.lint_tickets(checkout, args.stems))
            if result["exit_code"] == 2:
                first = result["refusals"][0]
                raise runner.Refusal(first["message"], first["paved_road"], code="lint_refused")
            value = {"valid": result["valid"], "total": result["total"], "valid_all": result["exit_code"] == 0, "findings": result["findings"]}
        elif name == "clutch_ticket_order":
            value = tickets.order_ticket(checkout, args.stem, priority=args.priority, runs_before=args.runs_before)
        elif name in {"clutch_ticket_confirm", "clutch_ticket_reject", "clutch_app_ticket_confirm", "clutch_app_ticket_reject"}:
            value = asyncio.run(runner.submit_verdict(args.stem, checkout, kill=name.endswith("reject"), extension=name.startswith("clutch_app_"), reason=getattr(args, "reason", None)))
        elif name == "clutch_box_suggest":
            id_, created = box.suggest(cfg.state_dir, fs, checkout.journal, args.summary)
            value = {"id": id_, "created": created}
        elif name == "clutch_box_dismiss":
            value = {"lines": asyncio.run(runner.dismiss_boxes(checkout, args.ids, lock_ctx_factory=runner._locked))}
        elif name == "clutch_box_triage":
            value = asyncio.run(_submit_only(checkout, "triage", ids=args.ids))
        elif name == "clutch_engine_start":
            pid, output = serve.start_detached(checkout.repo, cfg.state_dir, args.mode, config_path=self.config_path if checkout.repo == self.cwd else None, env=self.env, spawn=self.spawn)
            value = {"pid": pid, "output": output}
        elif name == "clutch_engine_control":
            value = observe.ping_engine(cfg.state_dir) if args.action == "ping" else asyncio.run(runner.control_engine(checkout, args.action))
        elif name == "clutch_engine_retro":
            value = asyncio.run(_submit_only(checkout, "retro"))
        else:
            text, catalog = self.prompt(checkout, ctx, args.kind, args.stems, args.name)
            value = catalog if catalog is not None else {"text": text}
            return value, text or json.dumps(value)
        value = _json(value)
        return value, json.dumps(value)

    def dispatch(self, method, params):
        if method == "initialize":
            self.client_supports_roots = isinstance(params.get("capabilities"), dict) and "roots" in params["capabilities"]
            requested = params.get("protocolVersion")
            return {
                "protocolVersion": requested if requested in {"2025-03-26", "2024-11-05"} else "2025-03-26",
                "capabilities": {"tools": {"listChanged": False}, "prompts": {"listChanged": False}, "resources": {"listChanged": False}},
                "serverInfo": {"name": "clutchwork", "version": version("clutchwork")},
            }
        if method == "resources/list":
            return {"resources": [{"uri": DASHBOARD_URI, "name": "ClutchWork dashboard", "mimeType": MCP_APP_MIME, "_meta": {"ui": {"prefersBorder": False}}}]}
        if method == "resources/read":
            if params.get("uri") != DASHBOARD_URI:
                raise InvalidParams("unknown resource")
            try:
                html = self.ui_html_path.read_text(encoding="utf-8")
                if not html:
                    raise ValueError("empty dashboard")
            except OSError, UnicodeError, ValueError:
                raise DomainError(
                    {
                        "code": "dashboard_unavailable",
                        "message": "Dashboard UI bundle is unavailable.",
                        "paved_road": "build the dashboard UI bundle before opening the dashboard (see docs/how-clutch-works.md)",
                    }
                ) from None
            return {"contents": [{"uri": DASHBOARD_URI, "mimeType": MCP_APP_MIME, "text": html}]}
        if method == "ping":
            return {}
        if method == "tools/list":
            return {
                "tools": [
                    {
                        "name": name,
                        "description": name.replace("_", " "),
                        "inputSchema": spec.model.model_json_schema(),
                        "_meta": {
                            "ui": {"visibility": list(spec.visibility), **({"resourceUri": DASHBOARD_URI} if name == "clutch_open_dashboard" else {})},
                            **(
                                {"com.google.antigravity/ui": {"entrypoints": [{"type": "aux_pane", "title": "ClutchWork"}, {"type": "global", "title": "ClutchWork"}]}}
                                if name == "clutch_open_dashboard"
                                else {}
                            ),
                        },
                    }
                    for name, spec in TOOLS.items()
                ]
            }
        if method == "prompts/list":
            result = []
            for kind in ask.KINDS:
                arguments = [{"name": "repo", "required": False}]
                if ask.TAKES[kind] != "none":
                    arguments.append({"name": "ids" if kind == "box" else "stem", "required": True})
                result.append({"name": kind, "description": ask.DESCRIPTIONS[kind], "arguments": arguments})
            result.append({"name": "host", "description": HOST_PROMPT_DESCRIPTION, "arguments": [{"name": "repo", "required": False}, {"name": "name", "required": False}]})
            return {"prompts": result}
        if method == "tools/call":
            name = params.get("name")
            if not isinstance(name, str) or name not in TOOLS:
                raise InvalidParams("unknown tool")
            try:
                args = TOOLS[name].model.model_validate(params.get("arguments", {}))
            except ValidationError as exc:
                if name == "clutch_app_config" and isinstance(params.get("arguments"), dict) and "updates" in params["arguments"]:
                    value = _error(runner.Refusal(str(exc), "supply valid retro or scheduler.parallel settings", code="invalid_config"))
                    return {"isError": True, "content": [{"type": "text", "text": value["message"]}], "structuredContent": value}
                raise InvalidParams(str(exc)) from None
            try:
                value, text = self.call_tool(name, args)
                return {"content": [{"type": "text", "text": text or "(empty)"}], "structuredContent": _json(value)}
            except (
                runner.Refusal,
                LockHeld,
                CommitLockTimeout,
                tickets.IntakeRefused,
                ProviderSetupError,
                ExecutableNotFound,
                hostfiles.MarkerCorruption,
                ConfigError,
                JournalCorruption,
                GitError,
                UnknownBoxId,
                ValueError,
            ) as exc:
                value = _error(exc)
                return {"isError": True, "content": [{"type": "text", "text": value["message"]}], "structuredContent": value}
        if method == "prompts/get":
            kind = params.get("name")
            if not isinstance(kind, str) or (kind not in ask.KINDS and kind != "host"):
                raise InvalidParams("unknown prompt")
            args = params.get("arguments", {})
            if kind == "host":
                if not isinstance(args, dict) or set(args) - {"repo", "name"} or any(not isinstance(value, str) for value in args.values()):
                    raise InvalidParams("invalid prompt arguments")
                try:
                    checkout, ctx = self.checkout(args.get("repo"))
                    text, catalog = self.prompt(checkout, ctx, "host", [], name=args.get("name"))
                    return {"description": HOST_PROMPT_DESCRIPTION, "messages": [{"role": "user", "content": {"type": "text", "text": text or json.dumps(catalog)}}]}
                except (runner.Refusal, ConfigError, JournalCorruption, GitError, UnknownBoxId) as exc:
                    raise DomainError(_error(exc)) from None
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


def check_server(server: ClutchMCPServer) -> dict[str, object]:
    try:
        listing = server.dispatch("tools/list", {})
        tools = listing.get("tools", []) if isinstance(listing, dict) else []
        if not isinstance(tools, list) or not any(isinstance(tool, dict) and tool.get("name") == "clutch_open_dashboard" for tool in tools):
            raise runner.Refusal("dashboard tool unavailable", "install a server with clutch_open_dashboard")
        result = server.dispatch("resources/read", {"uri": DASHBOARD_URI})
        contents = result.get("contents", []) if isinstance(result, dict) else []
        if not isinstance(contents, list) or not any(
            isinstance(item, dict) and item.get("uri") == DASHBOARD_URI and item.get("mimeType") == MCP_APP_MIME and isinstance(item.get("text"), str) and item["text"] for item in contents
        ):
            raise runner.Refusal("dashboard resource invalid", "build the dashboard UI bundle")
        return result
    except DomainError as exc:
        detail = exc.args[0] if exc.args and isinstance(exc.args[0], dict) else {}
        raise runner.Refusal(str(detail.get("message", "dashboard unavailable")), str(detail.get("paved_road", "build the dashboard UI bundle")), code=str(detail.get("code", "refusal"))) from None


def serve_stdio(*, stdin=None, stdout=None, **kwargs):
    stdin = stdin if stdin is not None else sys.stdin
    out = stdout if stdout is not None else sys.stdout
    server = ClutchMCPServer(**kwargs)
    roots_counter = 0
    pending_roots = set()
    write_lock = threading.Lock()

    def write(value):
        with write_lock:
            out.write(json.dumps(value) + "\n")
            out.flush()

    def respond(id_, method, params):
        try:
            result = server.dispatch(method, params)
            response = {"jsonrpc": "2.0", "id": id_, "result": result}
        except InvalidParams as exc:
            response = {"jsonrpc": "2.0", "id": id_, "error": {"code": -32602, "message": str(exc)}}
        except UnknownMethod:
            response = {"jsonrpc": "2.0", "id": id_, "error": {"code": -32601, "message": "Method not found"}}
        except DomainError as exc:
            response = {"jsonrpc": "2.0", "id": id_, "error": {"code": -32000, "message": "Domain refusal", "data": exc.args[0]}}
        except Exception:
            response = {"jsonrpc": "2.0", "id": id_, "error": {"code": -32603, "message": "Internal error"}}
        write(response)

    with redirect_stdout(sys.stderr), concurrent.futures.ThreadPoolExecutor() as pool:
        for line in stdin:
            if not line.strip():
                continue
            id_ = None
            try:
                try:
                    request = json.loads(line)
                except json.JSONDecodeError:
                    raise RPCError(-32700, "Parse error") from None
                if isinstance(request, dict) and request.get("jsonrpc") == "2.0" and "method" not in request and "result" in request:
                    if request.get("id") in pending_roots:
                        pending_roots.remove(request["id"])
                        result = request["result"]
                        if isinstance(result, dict) and isinstance(result.get("roots"), list):
                            server.roots = [
                                Path(unquote(uri.path))
                                for item in result["roots"]
                                if isinstance(item, dict) and isinstance(item.get("uri"), str)
                                for uri in [urlparse(item["uri"])]
                                if uri.scheme == "file"
                            ]
                    continue
                if not isinstance(request, dict) or request.get("jsonrpc") != "2.0" or not isinstance(request.get("method"), str):
                    raise RPCError(-32600, "Invalid Request")
                id_ = request.get("id")
                if "id" not in request:
                    if server.client_supports_roots and request["method"] in {"notifications/initialized", "notifications/roots/list_changed"}:
                        roots_counter += 1
                        root_id = f"roots-{roots_counter}"
                        pending_roots.add(root_id)
                        write({"jsonrpc": "2.0", "id": root_id, "method": "roots/list"})
                    continue
                params = request.get("params", {})
                if not isinstance(params, dict):
                    raise InvalidParams("params must be an object")
                if request["method"] == "tools/call":
                    _validate_tool(params)
                    pool.submit(respond, id_, request["method"], params)
                else:
                    respond(id_, request["method"], params)
            except InvalidParams as exc:
                write({"jsonrpc": "2.0", "id": id_, "error": {"code": -32602, "message": str(exc)}})
            except RPCError as exc:
                write({"jsonrpc": "2.0", "id": id_, "error": {"code": exc.code, "message": str(exc)}})
            except Exception:
                write({"jsonrpc": "2.0", "id": id_, "error": {"code": -32603, "message": "Internal error"}})


class RPCError(Exception):
    def __init__(self, code, message, data=None):
        super().__init__(message)
        self.code, self.data = code, data
