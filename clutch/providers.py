"""Provider layer: registry + routing, key-scoped child env, the cli adapters.

Session admission selects from the ordered route before its LLM effect. `CliAdapter` is the
shared base and the trust boundary -- write-grant derivation, redaction of both sinks (the captured
stream and the returned result), and the cost floor live there ONCE; each subclass is only its CLI's
argv contract and event-stream parse.
"""

import asyncio
import hashlib
import importlib.metadata
import json
import math
import os
import re
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING, Literal
from urllib.parse import quote
from uuid import uuid4

from pydantic import ValidationError

from clutch.config import Config, ConfigSnapshot, Provider, snapshot_config
from clutch.evidence import antigravity, claude, codex
from clutch.evidence.schema import Event
from clutch.evidence.store import EvidenceStore
from clutch.git import Git
from clutch.journal import EventType, last_transition, render_ts
from clutch.llm import TIERS, AgentEffort, AgentTier, LLMRequest, LLMResult
from clutch.llmeffect import member_index
from clutch.lockfile import CommitLock
from clutch.redact import Redactor, secret_names
from clutch.seams import Clock, ExecutableNotFound, FileSystem, GroupExec, ProcessExec
from clutch.specs import load_spec

if TYPE_CHECKING:
    from clutch.watchdog import EventConsumer

# Closed allowlist of tree-writing surfaces: every other surface is called read-only.
WRITING_SURFACES = frozenset({"implement"})
CODEX_EFFORT = {"low": "low", "medium": "medium", "high": "high", "max": "high"}

# The value prompt 1 authors when the operator stated none; it must never reach a model.
PLACEHOLDER = "OPERATOR-SETS-THIS"

FailureClass = Literal["rate_limited", "quota_exhausted", "outage", "auth_error", "model_error", "unclassified"]

FAILURE_MARKERS: tuple[tuple[FailureClass, tuple[str, ...]], ...] = (
    ("quota_exhausted", ("quota exhausted", "usage limit reached", "out of extra usage", "exhausted your daily quota")),
    ("rate_limited", ("rate limit", "too many requests", "resource_exhausted")),
    ("outage", ("service unavailable", "internal server error", "stream disconnected", "at capacity")),
    ("model_error", ("model unavailable", "model not found", "model is not supported", "modelnotfounderror")),
)


def engine_version() -> str:
    return importlib.metadata.version("clutchwork")


def spec_version(surface: str) -> str:
    return load_spec((Path(__file__).parent / "specs" / f"{surface}.md").read_text()).meta.version


@dataclass(frozen=True)
class CallCapture:
    key: str
    ticket: str | None
    candidates: tuple[str, ...]
    reason: Literal["first", "spill", "failover"]
    git: Git
    clock: Clock


class ProviderSetupError(Exception):
    """A config/setup refusal raised before any call runs: nothing was metered."""


class ProviderBudgetExceeded(Exception):
    """The eval remainder cannot admit this call; rerun within a fresh bounded run."""


class ProviderCallError(Exception):
    """The CLI ran and failed. `stderr_tail` is scrubbed."""

    def __init__(
        self,
        provider: str,
        message: str,
        *,
        rc: int,
        stderr_tail: str,
        failure_class: str | None = None,
        paved_road: str | None = None,
    ) -> None:
        super().__init__(f"{provider}: {message} (exit {rc}); stderr tail: {stderr_tail!r}")
        self.provider = provider
        self.rc = rc
        self.stderr_tail = stderr_tail
        self.failure_class = failure_class
        self.paved_road = paved_road


def child_env(
    env: Mapping[str, str],
    config: Config | ConfigSnapshot,
    serving: Provider | ConfigSnapshot | None = None,
) -> dict[str, str]:
    """INHERIT-MINUS-SECRETS: the full parent env minus every configured secret, plus only the serving call's own key.

    Every non-LLM child (checks, verification, replay) passes `serving=None` and gets no key at all.
    """
    out = {k: v for k, v in env.items() if k not in secret_names(config)}
    if serving is not None and serving.auth:
        if serving.auth not in env:
            raise ProviderSetupError(f"provider {serving.name!r} needs env var {serving.auth} and it is unset; export it before the run")
        out[serving.auth] = env[serving.auth]
    return out


@dataclass(frozen=True)
class Served:
    provider: Provider | ConfigSnapshot
    model: str


def _route(config, tier, surface, kind):
    for name in (surface, "review") if surface != "review" else (surface,):
        rows = [r for r in config.routing if r.tier == tier and r.surface == name]
        if kind is not None:
            matched = next((r for r in rows if r.kinds is not None and kind in r.kinds), None)
            if matched is not None:
                return matched
        matched = next((r for r in rows if r.kinds is None), None)
        if matched is not None:
            return matched
    raise ProviderSetupError(f"no routing row for tier {tier!r}, surface {surface!r}; add one under `routing:` in config.yaml")


def resolve(config: Config | ConfigSnapshot, tier: AgentTier, surface: str, kind: str | None = None) -> Served:
    """Resolve the first candidate of the matching route."""
    return _candidate(config, tier, surface, _route(config, tier, surface, kind).candidates[0])


def _candidate(config, tier, surface, cand):
    provider = next(p for p in config.providers if p.name == cand.provider)  # load_config checked the reference
    model = cand.model if cand.model is not None else getattr(provider.models_by_tier, tier)
    if PLACEHOLDER in (model, provider.auth):
        raise ProviderSetupError(f"routing for tier {tier!r}, surface {surface!r} resolves to provider {provider.name!r} still carrying {PLACEHOLDER}; set the operator values in config.yaml")
    return Served(provider, model)


def candidates(config, tier, surface, kind=None) -> tuple[Served, ...]:
    route = _route(config, tier, surface, kind)
    return tuple(_candidate(config, tier, surface, candidate) for candidate in route.candidates)


def panel_members(config, tier, surface, kind=None) -> tuple[Served, ...]:
    route = _route(config, tier, surface, kind)
    size = route.panel.size if route.panel is not None and route.surface == surface else 1
    selected = route.candidates[:size] if len(route.candidates) >= size else [route.candidates[0]] * size
    return tuple(_candidate(config, tier, surface, candidate) for candidate in selected)


def panel_slots_finding(config) -> str | None:
    for i, route in enumerate(config.routing):
        if route.panel is None or route.panel.size == 1:
            continue
        kind = route.kinds[0] if route.kinds else None
        try:
            members = panel_members(SimpleNamespace(routing=[route], providers=config.providers), route.tier, route.surface, kind)
        except ProviderSetupError:
            continue
        if all(member.provider.limits.concurrency == 1 for member in members):
            return f"routing.{i} panel members have limits.concurrency 1; raise limits.concurrency or add a second candidate on another provider"
    return None


def judge_independence_finding(config) -> str | None:
    for tier in dict.fromkeys(r.tier for r in config.routing if r.kinds is not None and "graphics" in r.kinds):
        try:
            implement = resolve(config, tier, "implement", "graphics")
            judge = resolve(config, tier, "review_visual", "graphics")
        except ProviderSetupError:
            continue
        if implement.provider.name == judge.provider.name and implement.model == judge.model:
            return f"graphics implement and review_visual for tier {tier!r} both use provider {judge.provider.name!r} and model {judge.model!r}; route the judge to a different provider or model"
    return None


def conduct_file(provider: str) -> str:
    return "CLAUDE.md" if provider in {"claude", "qwen"} else "AGENTS.md"


def routed_conduct_paths(config: Config | ConfigSnapshot, checkout: Path) -> tuple[Path, ...]:
    """Select each resolved CLI's conduct file once; unrouted declarations do not participate."""
    return tuple(
        dict.fromkeys(checkout / conduct_file(served.provider.name) for route in config.routing for served in candidates(config, route.tier, route.surface, route.kinds[0] if route.kinds else None))
    )


class ProviderDrought(Exception):
    """A pre-effect routing refusal, carried to the existing failure owner."""

    def __init__(self, tier, surface, refusal):
        self.record = {"tier": tier, "surface": surface, "providers": list(refusal.providers)}
        self.waited_seconds = refusal.waited_seconds
        self.deadline = refusal.open_until
        self.paved_road = refusal.paved_road
        super().__init__(f"provider_drought: {', '.join(refusal.providers)}; {self.paved_road}")


class ProviderSession:
    """One idle registry, admission owner and Timer lifetime per lock holder."""

    def __init__(self, config, *, journal, clock, sleep, timers):
        from clutch.thresh import Thresh

        self.journal, self.clock, self.sleep, self.timers = journal, clock, sleep, timers
        self.thresh = Thresh(config, journal=journal, clock=clock, sleep=sleep)
        self.auth_excluded: set[str] = set()
        self.auth_position: int | None = None
        self.active = False
        self.thresh.unavailable = self.unavailable
        self.thresh.on_outcome = self.outcome
        self.waits: set[asyncio.Task] = set()
        self._holds: dict[str, datetime] = {}
        self._held_seconds: dict[str, float] = {}
        self._preflight_lock = asyncio.Lock()
        self._preflight_config = None
        self._preflight_versions = {}

    def live_wait(self, prefix):
        return (
            self.thresh.live_wait(prefix)
            + sum(seconds for key, seconds in self._held_seconds.items() if key.startswith(prefix))
            + sum(max(0, (self.clock() - started).total_seconds()) for key, started in self._holds.items() if key.startswith(prefix))
        )

    async def wait_until(self, deadline):
        async def wait():
            while self.clock() < deadline:
                await self.sleep((deadline - self.clock()).total_seconds())
            self.timers.fire_due()

        task = asyncio.create_task(wait())
        self.waits.add(task)
        try:
            await asyncio.shield(task)
        finally:
            from clutch.driver import _observe

            task.cancel()
            await _observe(asyncio.gather(task, return_exceptions=True))
            self.waits.discard(task)

    async def close(self):
        from clutch.driver import _observe

        tasks = tuple(self.waits)
        for task in tasks:
            task.cancel()
        await _observe(asyncio.gather(*tasks, return_exceptions=True))
        self.waits.clear()

    async def preflight_once(self, config, llm, probe):
        snapshot = snapshot_config(config) if isinstance(config, Config) else config
        key = (snapshot.providers, snapshot.routing)
        async with self._preflight_lock:
            if self._preflight_config == key:
                for name, adapter in llm._adapters.items():
                    adapter.cli_version = self._preflight_versions[name]
                return []
            self._preflight_config = None
            self._preflight_versions = {}
            problems = await probe()
            if not problems:
                self._preflight_config = key
                self._preflight_versions = {name: adapter.cli_version for name, adapter in llm._adapters.items()}
            return problems

    def preflight_passed(self):
        if self.auth_position is None:
            self.auth_position = len(self.journal.read())

    def cooling(self):
        self.timers.fire_due()
        return {timer.body.timer_id.split("/")[1]: timer.deadline for timer in self.timers.pending.values() if timer.body.timer_id.startswith("provider-cooldown/")}

    def exclusions(self):
        if self.auth_position is not None:
            history = self.journal.read()
            self.auth_excluded.update(
                e.body["provider"]
                for e in history[self.auth_position :]
                if e.type == EventType.SIGNAL and e.body.get("signal") == "provider_call_outcome" and e.body.get("failure_class") == "auth_error"
            )
            self.auth_position = len(history)
        return self.auth_excluded

    def unavailable(self, name):
        cooling = self.cooling()
        if name in self.exclusions():
            return True, cooling.get(name), ADAPTERS[name].LOGIN_ROAD
        if name in cooling:
            return True, cooling[name], f"wait until {render_ts(cooling[name])}"
        return False, None, None

    def quota(self, provider):
        if provider.name not in self.cooling():
            deadline = self.clock() + timedelta(minutes=provider.limits.quota_window_minutes)
            self.timers.arm(f"provider-cooldown/{provider.name}/{render_ts(deadline)}", deadline, ticket=None)

    def outcome(self, served, failure):
        # Thresh invokes this only after its sole outcome append succeeds.
        if failure == "quota_exhausted":
            self.quota(served.provider)
        elif failure == "auth_error":
            self.auth_excluded.add(served.provider.name)

    def drought(self, config, tier, surface):
        from clutch.thresh import UnavailableRoute

        route = candidates(config, tier, surface)
        refusal = self.thresh._select(route, 0, 0)
        return ProviderDrought(tier, surface, refusal) if isinstance(refusal, UnavailableRoute) else None

    def park(self, stem, drought):
        history = self.journal.read()
        previous = last_transition(history, stem) or {}
        if previous.get("provider_drought") != drought.record:
            self.journal.append(EventType.STATE_TRANSITION, {"to": "infra_error", "reason": "provider_drought", "provider_drought": drought.record}, ticket=stem, key=None)


@dataclass(frozen=True)
class Parsed:
    text: str
    input_tokens: int | None
    output_tokens: int | None
    usd: float | None  # None: the stream reports no cost, so the declared estimate charges
    model: str | None = None


def parsed_from_events(events: list[Event], read_blob: Callable[[str], bytes]) -> Parsed:
    closing = next((i for i in range(len(events) - 1, -1, -1) if events[i].kind in ("result", "usage") and events[i].status is not None), None)
    if closing is None:
        error = next((e for e in reversed(events) if e.kind == "error" and e.text_blob is not None), None)
        prefix = read_blob(error.text_blob).decode() + ": " if error else ""
        raise ValueError(prefix + "no terminal result event in the stream")
    event = events[closing]
    if event.status == "error":
        raise ValueError(f"{event.status}: {read_blob(event.text_blob).decode() if event.text_blob is not None else ''}")
    if event.text_blob is None:
        raise ValueError("success result has no text blob")
    tokens = event.tokens
    if tokens is None and closing and events[closing - 1].kind == "usage" and events[closing - 1].native_type == event.native_type:
        tokens = events[closing - 1].tokens
    tokens = tokens if isinstance(tokens, dict) else {}
    inputs = [tokens.get(k) for k in ("input_uncached", "input_cache_read", "input_cache_write")]
    known = [n for n in inputs if n is not None]
    return Parsed(read_blob(event.text_blob).decode(), sum(known) if known else None, tokens.get("output_total"), event.usd, event.model)


CLAUDE_ALIASES = ("haiku", "sonnet", "opus", "fable")


@dataclass(frozen=True)
class ModelListing:
    models: dict[str, str]
    problems: tuple[str, ...]


class CliAdapter:
    """Shared base for one agent CLI. Subclasses supply `binary`, `reports_cost`, `argv`, `parse`."""

    @classmethod
    async def list_models(cls, *, exec_: ProcessExec, env: Mapping[str, str], cwd: Path) -> ModelListing:
        raise NotImplementedError

    AUTH_ENV: str | None = None
    TIER_LABELS: dict[str, str] | None = None
    uses_base_url = False
    binary: str
    PACKAGE: str | None = None
    reports_cost: bool
    AUTH_MARKERS: tuple[str, ...]
    LOGIN_ROAD: str

    def __init__(
        self,
        provider: Provider | ConfigSnapshot,
        *,
        config: Config | ConfigSnapshot,
        exec_: GroupExec,
        fs: FileSystem,
        redactor: Redactor,
        env: Mapping[str, str],
        cwd: Path,
        timeout: float,
    ) -> None:
        if provider.base_url and not self.uses_base_url:
            raise ProviderSetupError(f"provider {provider.name!r} does not use base_url; remove base_url from that provider in config.yaml")
        if not provider.base_url and self.uses_base_url:
            raise ProviderSetupError(f"provider {provider.name!r} needs base_url; set base_url in config.yaml")
        if not self.reports_cost and provider.limits.est_cost_per_call_usd is None:
            raise ProviderSetupError(f"provider {provider.name!r}: the {self.binary} stream reports no cost, so limits.est_cost_per_call_usd is required; declare a flat per-call estimate")
        self.provider = provider
        self._config = config
        self._exec = exec_
        self._fs = fs
        self._redactor = redactor
        self._env = env
        self._cwd = cwd
        self._timeout = timeout
        self.cli_version: str | None = None
        self._pgids: set[int] = set()

    def call_env(self, writes: bool) -> dict[str, str]:
        return tool_env(child_env(self._env, self._config, self.provider), self._cwd)

    def argv(self, model: str, effort: AgentEffort, writes: bool) -> list[str]:
        raise NotImplementedError

    def parse(self, out: str) -> Parsed:
        """Raise `ValueError` naming the failure when the stream carries no successful result."""
        blobs = {}

        def put_blob(value: bytes) -> str:
            key = str(len(blobs))
            blobs[key] = value
            return key

        try:
            events = self.normalizer(out.encode(), None, put_blob)
        except (KeyError, TypeError, AttributeError, ValidationError) as exc:
            raise ValueError(f"stream could not be normalized: {exc}") from exc
        return parsed_from_events(events, blobs.__getitem__)

    def within_budget(self, req: LLMRequest) -> bool:
        budget = req.budget_usd
        return budget is None or (budget > 0 and (self.reports_cost or self.provider.limits.est_cost_per_call_usd <= budget))

    def check_budget(self, req: LLMRequest) -> None:
        if not self.within_budget(req):
            raise ProviderBudgetExceeded("remaining eval budget cannot admit the declared estimate; rerun the bounded eval")

    async def invoke(self, req: LLMRequest, model: str, *, consumer: "EventConsumer | None" = None, capture: CallCapture | None = None) -> LLMResult:
        self.check_budget(req)
        budget = req.budget_usd
        writes = req.surface in WRITING_SURFACES
        argv = self.argv(model, req.effort, writes)
        if budget is not None and self.reports_cost:
            argv.extend(["--max-budget-usd", str(budget)])
        if isinstance(self, ClaudeAdapter):
            argv.extend(["--name", self.session_name(req.surface, req.subject)])
        if writes and req.worktree is None:
            raise ProviderSetupError(f"surface {req.surface!r} writes the tree but the request carries no worktree")
        prompt = self._config.state_dir / "evidence" / "scratch" / f"{uuid4().hex}.md"
        index = prompt.with_suffix(".index")
        rendered = self._redactor.scrub(req.rendered)
        self._fs.write(prompt, rendered.encode())
        cwd = req.worktree if writes else self._cwd
        pgids: set[int] = set()
        store = None
        started = None
        rc = None
        out = err = ""
        parsed = None
        failure = None
        returned = False
        start_written = False
        native_id_saved = False
        times = []
        rusage = None

        def record_rusage(value):
            nonlocal rusage
            rusage = value

        def spawned(pgid: int) -> None:
            pgids.add(pgid)
            self._spawned(pgid)

        def stdout_line(line: str) -> None:
            nonlocal native_id_saved
            if capture is not None and start_written and not native_id_saved:
                try:
                    event = json.loads(line)
                except ValueError:
                    event = None
                if isinstance(event, dict):
                    ids = {name: event.get(name) if isinstance(event.get(name), str) else None for name in ("session_id", "thread_id")}
                    if not ids["session_id"] and isinstance(event.get("conversation_id"), str) and event["conversation_id"]:
                        ids["session_id"] = event["conversation_id"]
                    if any(value is not None for value in ids.values()):
                        store.write_record(key, "start", {**start_data, "native_ids": ids}, replace=True)
                        native_id_saved = True
            if capture is not None:
                times.append(int((capture.clock() - started).total_seconds() * 10**9))
            if consumer is not None:
                self._forward(line, consumer)

        try:
            env = self.call_env(writes)
            if capture is not None:
                store = EvidenceStore(self._config.state_dir, self._fs, self._fs.read_bytes, self._fs.size, self._redactor.scrub)
                key = capture.key
                suffix = 1
                entries = self._fs.entries(store.root / "calls")
                while quote(key, safe="") in entries:
                    suffix += 1
                    key = f"{capture.key}#{suffix}"
                _, group, run_seq, surface, attempt, call = capture.key.split("/")
                tree_before = await capture.git.tree_id(cwd, index)
                main_sha = await capture.git.rev_parse(cwd, "main")
                base_sha = await capture.git.rev_parse(cwd, "HEAD")
                started = capture.clock()
                start_data = {
                    "schema": "clutch.evidence.call/1.0",
                    "id": capture.key,
                    "group": group,
                    "stem": capture.ticket,
                    "run_seq": int(run_seq) if run_seq.isdecimal() else run_seq,
                    "surface": surface,
                    "attempt": int(attempt),
                    "call": int(call),
                    "engine": {"version": engine_version(), "spec": f"{surface}.md", "spec_version": spec_version(surface)},
                    "route": {
                        "tier": req.tier,
                        "effort": req.effort,
                        "candidates": list(capture.candidates),
                        "chosen": self.provider.name,
                        "reason": capture.reason,
                        "config_sha": hashlib.sha256(repr(snapshot_config(self._config)).encode()).hexdigest(),
                    },
                    "provider": {
                        "name": self.provider.name,
                        "adapter": type(self).__name__,
                        "kind": self.provider.kind,
                        "package": self.provider.package,
                        "cli_version": self.cli_version,
                        "billing": "local" if self.uses_base_url else "metered" if self.provider.auth else "subscription",
                    },
                    "model": {"requested": model},
                    "process": {
                        "argv": [self._redactor.scrub(arg) for arg in argv],
                        "env_names": sorted(env),
                        "cwd": str(cwd),
                        "timeout_s": int(self._timeout),
                        "writes": writes,
                        "isolated": False,
                        "conduct_file": conduct_file(self.provider.name),
                    },
                    "repo": {"main_sha": main_sha, "base_sha": base_sha, "tree_before": tree_before},
                    "prompt": {"blob": store.put_blob(rendered.encode()), "chars": len(rendered), "bytes": len(rendered.encode())},
                    "clock": {"wall_start": render_ts(started), "mono_start_ns": int(started.timestamp() * 10**9)},
                }
                store.write_record(key, "start", start_data)
                start_written = True
            rc, out, err = await self._exec.run(
                argv,
                cwd=cwd,
                env=env,
                timeout=self._timeout,
                stdin_path=prompt,
                on_spawn=spawned,
                **({"on_stdout_line": stdout_line} if capture is not None or consumer is not None else {}),
                **({"on_rusage": record_rusage} if capture is not None else {}),
            )
            returned = True
            out, err = self._redactor.scrub(out), self._redactor.scrub(err)
            tail = err[-2000:]
            if rc != 0:
                # A CLI may report its failure in the event stream, not stderr: carry that message forward.
                try:
                    parsed = self.parse(out)
                    message = "nonzero exit"
                except ValueError as e:
                    message = f"nonzero exit: {e}"
                self._raise_call_error(message, rc=rc, stderr_tail=tail)
            try:
                parsed = self.parse(out)
            except ValueError as e:
                self._raise_call_error(str(e), rc=rc, stderr_tail=tail)
            usd = parsed.usd if parsed.usd is not None else self.provider.limits.est_cost_per_call_usd
            if usd is None:
                self._raise_call_error(
                    "stream reported no cost and limits.est_cost_per_call_usd is unset; declare the estimate",
                    rc=rc,
                    stderr_tail=tail,
                )
            return LLMResult(
                # Scrubbed BEFORE it becomes the result: the one version that ever exists. Again after
                # decoding, since a JSON-escaped secret survives the raw-stream scrub.
                text=self._redactor.scrub(parsed.text),
                input_tokens=parsed.input_tokens,
                output_tokens=parsed.output_tokens,
                provider=self.provider.name,
                model=parsed.model if parsed.model is not None else model,
                usd=usd,
            )
        except BaseException as exc:
            failure = exc
            if not returned:
                out, err = getattr(exc, "process_capture", ("", ""))
            raise
        finally:
            self._pgids.difference_update(pgids)
            try:
                if start_written:
                    out, err = self._redactor.scrub(out), self._redactor.scrub(err)
                    ended = capture.clock()
                    repo = None
                    if writes and returned:
                        tree_after = await capture.git.tree_id(cwd, index)
                        repo = {"tree_after": tree_after, "changed_paths": await capture.git.tree_changes(cwd, tree_before, tree_after)}
                    events = _events(out)

                    def first(name):
                        return next((e[name] for e in events if isinstance(e.get(name), str)), None)

                    served = first("model") or next((e["init"]["model"] for e in events if isinstance(e.get("init"), dict) and isinstance(e["init"].get("model"), str)), None)
                    status = (
                        ("ok" if rc == 0 else "nonzero" if rc > 0 else "killed")
                        if returned
                        else "timeout"
                        if isinstance(failure, TimeoutError)
                        else "spawn_error"
                        if isinstance(failure, ExecutableNotFound)
                        else "killed"
                    )
                    store.write_record(
                        key,
                        "end",
                        {
                            "schema": "clutch.evidence.call/1.0",
                            "id": capture.key,
                            "exit": {
                                "status": status,
                                "code": rc,
                                "signal": -rc if rc is not None and rc < 0 else None,
                                "failure_class": failure.failure_class if isinstance(failure, ProviderCallError) else None,
                            },
                            "clock": {"wall_end": render_ts(ended), "mono_end_ns": int(ended.timestamp() * 10**9), "wall_ms": int((ended - started).total_seconds() * 1000)},
                            "rusage": rusage,
                            "raw": {
                                "stdout": store.put_blob(out.encode()),
                                "stderr": store.put_blob(err.encode()),
                                "stdout_times": store.put_blob(json.dumps(times).encode()),
                                "lines": len(out.splitlines()),
                                "non_json_lines": len(out.splitlines()) - len(events),
                            },
                            "repo": repo,
                            "model": {"served": served, "served_source": "stream" if served is not None else "none"},
                            "native_ids": {"session_id": first("session_id") or first("conversation_id"), "thread_id": first("thread_id")},
                            "parsed": {
                                "text_chars": len(parsed.text) if parsed else 0,
                                "input_tokens": parsed.input_tokens if parsed else None,
                                "output_tokens": parsed.output_tokens if parsed else None,
                                "usd": parsed.usd if parsed else None,
                            },
                        },
                    )
            finally:
                self._fs.remove(prompt)
                self._fs.remove(index)

    def _spawned(self, pgid: int) -> None:
        self._pgids.add(pgid)

    def _forward(self, line: str, consumer: "EventConsumer") -> None:
        for event in _events(line):
            # Scrub decoded strings too: JSON escaping can hide a configured secret in the raw line.
            consumer.consume(self._scrub_event(event))

    def _scrub_event(self, value):
        if isinstance(value, str):
            return self._redactor.scrub(value)
        if isinstance(value, dict):
            return {self._redactor.scrub(k): self._scrub_event(v) for k, v in value.items()}
        if isinstance(value, list):
            return [self._scrub_event(v) for v in value]
        return value

    def classify_failure(self, message: str, *, rc: int, stderr_tail: str) -> ProviderCallError:
        """Classify only failed diagnostics, never successful output."""
        message = self._redactor.scrub(message)
        tail = stderr_tail[-2000:]
        diagnostic = f"{tail}\n{message}".lower()
        markers = (("auth_error", self.AUTH_MARKERS), *FAILURE_MARKERS)
        failure = next((kind for kind, words in markers if any(w in diagnostic for w in words)), "unclassified")
        road = None
        if failure == "auth_error":
            road = self.LOGIN_ROAD
        elif failure == "model_error":
            road = f"fix provider {self.provider.name!r}'s model route in config.yaml, then retry"
        elif failure != "unclassified":
            road = f"wait for provider {self.provider.name!r} to recover from {failure}, then retry"
        return ProviderCallError(self.provider.name, message, rc=rc, stderr_tail=tail, failure_class=failure, paved_road=road)

    def parsed_failure(self, out: str, *, rc: int, stderr_tail: str) -> ProviderCallError | None:
        """Direct construction seam; invoke retains its existing production error handling."""
        try:
            self.parse(out)
        except ValueError as exc:
            return self.classify_failure(str(exc), rc=rc, stderr_tail=stderr_tail)
        if rc != 0:
            return self.classify_failure("nonzero exit", rc=rc, stderr_tail=stderr_tail)
        return None

    def _raise_call_error(self, message: str, *, rc: int, stderr_tail: str) -> None:
        raise self.classify_failure(message, rc=rc, stderr_tail=stderr_tail)

    def abort(self) -> None:
        for pgid in tuple(self._pgids):
            self._exec.kill_group(pgid)


def _events(out: str) -> list[dict]:
    # Non-JSON lines (a CLI warning on stdout) stay in the capture; success still requires the terminal event.
    events = []
    for line in out.splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if isinstance(event, dict):
            events.append(event)
    return events


class ClaudeAdapter(CliAdapter):
    normalizer = staticmethod(claude.normalize)
    TIER_LABELS = {"low": "haiku", "medium": "sonnet", "high": "opus", "max": "fable"}
    PACKAGE = "@anthropic-ai/claude-code"
    binary = "claude"
    reports_cost = True
    AUTH_MARKERS = ("invalid api key", "please run /login", "not logged in", "oauth token has expired")
    LOGIN_ROAD = "run claude interactively and complete /login, then `clutch engine drain`"

    @staticmethod
    def session_name(surface: str, subject: str) -> str:
        return f"Clutch {surface.replace('_', ' ').title()} {subject}"

    @classmethod
    async def list_models(cls, *, exec_: ProcessExec, env: Mapping[str, str], cwd: Path) -> ModelListing:
        async def resolve(alias):
            rc, out, _ = await exec_.run(
                [
                    cls.binary,
                    "-p",
                    PROBE_PROMPT,
                    "--output-format",
                    "stream-json",
                    "--verbose",
                    "--model",
                    alias,
                    "--tools",
                    "Read",
                    "--permission-mode",
                    "dontAsk",
                    "--name",
                    cls.session_name("preflight", alias),
                ],
                cwd=cwd,
                env=tool_env(env, cwd),
                timeout=PREFLIGHT_TIMEOUT_S,
            )
            events = _events(out)
            result = next((e for e in reversed(events) if e.get("type") == "result"), None)
            init = next((e for e in events if e.get("type") == "system" and e.get("subtype") == "init"), {})
            model = init.get("model")
            if result and result.get("subtype") == "success" and not result.get("is_error") and isinstance(model, str) and model:
                return alias, model, None
            reason = f"{result.get('subtype')}: {result.get('result')}" if result else f"no terminal result event (rc {rc})"
            return alias, None, f"{alias}: {reason}"

        results = await asyncio.gather(*(resolve(alias) for alias in CLAUDE_ALIASES))
        return ModelListing({alias: model for alias, model, _ in results if model is not None}, tuple(problem for _, _, problem in results if problem is not None))

    def argv(self, model: str, effort: AgentEffort, writes: bool) -> list[str]:
        # No effort flag: effort is recorded in provenance only. stream-json under -p requires --verbose.
        grant = ["--permission-mode", "bypassPermissions"] if writes else ["--tools", "Read", "Grep", "Glob", "LS", "--permission-mode", "dontAsk"]
        return [self.binary, "-p", "--output-format", "stream-json", "--verbose", "--model", model, *grant]


class CodexAdapter(CliAdapter):
    normalizer = staticmethod(codex.normalize)
    PACKAGE = "@openai/codex"
    binary = "codex"
    reports_cost = False
    AUTH_MARKERS = ("not logged in", "401 unauthorized", "token has expired")
    LOGIN_ROAD = "run codex login, then `clutch engine drain`"

    @classmethod
    async def list_models(cls, *, exec_: ProcessExec, env: Mapping[str, str], cwd: Path) -> ModelListing:
        rc, out, err = await exec_.run([cls.binary, "debug", "models"], cwd=cwd, env=tool_env(env, cwd), timeout=PREFLIGHT_TIMEOUT_S)
        if rc:
            lines = [line for line in err.splitlines() if line.strip()]
            return ModelListing({}, (f"codex debug models: {lines[-1] if lines else ''}",))
        try:
            entries = json.loads(out)["models"]
            models = {entry["slug"]: entry["slug"] for entry in sorted(entries, key=lambda entry: entry["priority"]) if entry["visibility"] == "list"}
        except (ValueError, KeyError, TypeError) as exc:
            return ModelListing({}, (f"codex debug models: {exc}",))
        return ModelListing(models, ())

    def argv(self, model: str, effort: AgentEffort, writes: bool) -> list[str]:
        grant = ["--dangerously-bypass-approvals-and-sandbox"] if writes else ["--sandbox", "read-only", "-c", "approval_policy=never"]
        # Trailing `-`: the prompt is read from stdin.
        return [self.binary, "exec", "--json", "-m", model, "-c", f"model_reasoning_effort={CODEX_EFFORT[effort]}", *grant, "-"]


class QwenAdapter(ClaudeAdapter):
    TIER_LABELS = None
    PACKAGE = "@qwen-code/qwen-code"
    binary = "qwen"
    reports_cost = False
    uses_base_url = True
    AUTH_MARKERS = ()
    LOGIN_ROAD = "follow clutch/docs/host-qwen.md, then run clutch engine drain"

    @classmethod
    async def list_models(cls, *, exec_: ProcessExec, env: Mapping[str, str], cwd: Path) -> ModelListing:
        try:
            rc, out, err = await exec_.run(["ollama", "list"], cwd=cwd, env=tool_env(env, cwd), timeout=PREFLIGHT_TIMEOUT_S)
        except ExecutableNotFound:
            return ModelListing({}, ("ollama is not on PATH; run `ollama list` where Ollama runs (clutch/docs/host-qwen.md) and set models_by_tier by hand",))
        if rc:
            lines = [line for line in err.splitlines() if line.strip()]
            return ModelListing({}, (lines[-1] if lines else "",))
        names = [line.split()[0] for line in out.splitlines()[1:] if line.strip()]
        return ModelListing({name: name for name in names}, ())

    def argv(self, model: str, effort: AgentEffort, writes: bool) -> list[str]:
        return [
            "qwen",
            "--auth-type",
            "openai",
            "--openai-base-url",
            self.provider.base_url,
            "--openai-api-key",
            "ollama",
            "-m",
            model,
            "-o",
            "stream-json",
            "--approval-mode",
            "yolo" if writes else "plan",
            "--chat-recording",
            "false",
        ]

    def call_env(self, writes: bool) -> dict[str, str]:
        return {**super().call_env(writes), "QWEN_CODE_SYSTEM_SETTINGS_PATH": str((Path(__file__).parent / "qwen-settings.json").resolve())}


class AntigravityAdapter(CliAdapter):
    normalizer = staticmethod(antigravity.normalize)
    PACKAGE = None
    binary = "agy"
    reports_cost = False
    AUTH_ENV = None
    AUTH_MARKERS = ("please sign in", "not signed in", "authentication required", "unauthenticated")
    LOGIN_ROAD = "run agy interactively to sign in, then `clutch engine drain`"

    @classmethod
    async def list_models(cls, *, exec_: ProcessExec, env: Mapping[str, str], cwd: Path) -> ModelListing:
        rc, out, err = await exec_.run([cls.binary, "models"], cwd=cwd, env=tool_env(env, cwd), timeout=PREFLIGHT_TIMEOUT_S)
        if rc:
            lines = [line.rsplit("\r", 1)[-1].strip() for line in (out + "\n" + err).split("\n")]
            return ModelListing({}, (f"agy models: {next((line for line in reversed(lines) if line), '')}",))
        lines = [line.rsplit("\r", 1)[-1].strip() for line in out.split("\n")]
        models = {line.split()[0]: line.split()[0] for line in lines if line}
        return ModelListing(models, () if models else ("agy models: no models listed",))

    def argv(self, model: str, effort: AgentEffort, writes: bool) -> list[str]:
        return ["agy", "--output-format", "stream-json", "--input-format", "text", "--model", model, "--mode", *(["auto", "--dangerously-skip-permissions"] if writes else ["plan"])]


ADAPTERS: dict[str, type[CliAdapter]] = {"claude": ClaudeAdapter, "codex": CodexAdapter, "qwen": QwenAdapter, "antigravity": AntigravityAdapter}


PROBE_PROMPT = "Reply with the single word ok."
PREFLIGHT_TIMEOUT_S = 120.0
INSTALL_TIMEOUT_S = 600.0


def tool_env(env: Mapping[str, str], checkout: Path) -> dict[str, str]:
    path = str(checkout / "node_modules" / ".bin")
    return {**env, "PATH": path + os.pathsep + env["PATH"] if "PATH" in env else path}


def installed_version(out: str, err: str) -> str | None:
    match = re.search(r"\d+\.\d+\.\d+", out + err)
    return match.group(0) if match else None


@dataclass(frozen=True)
class CliStatus:
    name: str
    package: str | None
    binary: str
    where: Literal["project", "system", "absent"]
    version: str | None


def suggest_config(statuses: Sequence[CliStatus], listings: Mapping[str, ModelListing]) -> str:
    present = [status for status in statuses if status.where != "absent"]
    if not present:
        raise ValueError("no provider CLI found")
    lines = [
        "# Suggested by clutch config init from the provider CLIs found; edit models, checks and routing, then run clutch host doctor and clutch provider probe.",
        "schema_version: 1",
        "state_dir: .clutch",
        "providers:",
    ]
    for status in present:
        adapter = ADAPTERS[status.name]
        listing = listings[status.name]
        lines.extend([f"  - name: {status.name}", "    kind: cli"])
        if adapter.PACKAGE is not None:
            lines.append(f"    package: '{adapter.PACKAGE}'")
        if adapter.AUTH_ENV:
            lines.append(f"    auth: {adapter.AUTH_ENV}")
        if adapter.uses_base_url:
            lines.append("    base_url: http://localhost:11434/v1  # clutch/docs/host-qwen.md")
        first = next(iter(listing.models.values()), PLACEHOLDER)
        models = [listing.models.get(adapter.TIER_LABELS[tier], PLACEHOLDER) if adapter.TIER_LABELS else first for tier in TIERS]
        row = "    models_by_tier: {" + ", ".join(f"{tier}: {model or PLACEHOLDER}" for tier, model in zip(TIERS, models, strict=True)) + "}"
        if listing.models:
            row += "  # served: " + " ".join(" ".join(listing.models.values()).split())
        lines.append(row)
        lines.extend("    # " + " ".join(problem.split()) for problem in listing.problems)
        if adapter.reports_cost:
            lines.append("    limits: {concurrency: 1}")
        else:
            estimate = "0" if adapter.uses_base_url else "0.25"
            lines.append(f"    limits: {{concurrency: 1, est_cost_per_call_usd: {estimate}}}  # {adapter.binary} reports no cost: edit the estimate")
    lines.append("routing:")
    candidates = ", ".join(f"{{provider: {status.name}}}" for status in present)
    for tier in TIERS:
        for surface in ("implement", "review"):
            lines.append(f"  - {{tier: {tier}, surface: {surface}, candidates: [{candidates}]}}")
    lines.extend(["review: {}  # add your host's checks: clutch/docs/host-contract.md", "merge: {}", "engine_plane_safety_inventory: [config.yaml]"])
    return "\n".join(lines) + "\n"


async def cli_status(name: str, *, exec_: ProcessExec, env: Mapping[str, str], cwd: Path) -> CliStatus:
    adapter = ADAPTERS[name]
    try:
        _, out, err = await exec_.run([adapter.binary, "--version"], cwd=cwd, env=tool_env(env, cwd), timeout=PREFLIGHT_TIMEOUT_S)
    except ExecutableNotFound:
        return CliStatus(name, adapter.PACKAGE, adapter.binary, "absent", None)
    where = "project" if (cwd / "node_modules" / ".bin" / adapter.binary).is_file() else "system"
    return CliStatus(name, adapter.PACKAGE, adapter.binary, where, installed_version(out, err))


class ProviderLLM:
    """Snapshot-local adapters sharing one session's ordered provider admission."""

    kind: Literal["api", "cli"] = "cli"

    def __init__(
        self,
        config: Config | ConfigSnapshot,
        *,
        exec_: GroupExec,
        fs: FileSystem,
        env: Mapping[str, str],
        cwd: Path,
        timeout: float,
        session: ProviderSession,
    ) -> None:
        if not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("provider timeout must be positive and finite")
        self.session, self._timeout = session, timeout
        session.active = True
        session.thresh.configure(config)
        self._config = config
        self._exec, self._env, self._cwd = exec_, env, cwd
        self.preflight_notices: list[str] = []
        redactor = Redactor.from_config(config, env)
        self._adapters: dict[str, CliAdapter] = {}
        for p in config.providers:
            if p.name not in ADAPTERS:
                raise ProviderSetupError(f"provider {p.name!r} has no shipped cli adapter; name a provider one of {sorted(ADAPTERS)}")
            self._adapters[p.name] = ADAPTERS[p.name](
                p,
                config=config,
                exec_=exec_,
                fs=fs,
                redactor=redactor,
                env=env,
                cwd=cwd,
                timeout=timeout,
            )
        self._active: CliAdapter | None = None

    async def preflight(self) -> list[str]:
        """Every routed (provider, model) answering a probe; each cli compared with its latest release.

        Returns each refusal (a failing probe) with its paved road; a stale cli whose probes pass is only a
        notice, left on `preflight_notices` (a newer release can lag its platform build).
        """
        problems: list[str] = []
        notices = self.preflight_notices = []
        for adapter in self._adapters.values():
            if adapter.provider.name in self.session.exclusions():
                continue
            package = adapter.provider.package
            _, out, err = await self._exec.run([adapter.binary, "--version"], cwd=self._cwd, env=tool_env(child_env(self._env, self._config), self._cwd), timeout=PREFLIGHT_TIMEOUT_S)
            installed = adapter.cli_version = installed_version(out, err)
            if package is None:
                continue
            try:
                _, latest, _ = await self._exec.run(["pnpm", "view", str(package), "version"], cwd=self._cwd, env=child_env(self._env, self._config), timeout=PREFLIGHT_TIMEOUT_S)
            except TimeoutError, ExecutableNotFound:
                continue
            if not latest.strip() or installed is None or installed != latest.strip():
                notices.append(f"{adapter.binary} {installed or '(unknown)'} is not the latest release {latest.strip() or '(unreadable)'} -- run: clutch provider install {adapter.provider.name}")
        probed: set[tuple[str, str]] = set()
        probes = []
        for route in self._config.routing:
            for cand in route.candidates:
                if cand.provider in self.session.exclusions():
                    continue
                adapter = self._adapters[cand.provider]
                model = cand.model or getattr(adapter.provider.models_by_tier, route.tier)
                if (cand.provider, model) in probed:
                    continue
                probed.add((cand.provider, model))
                req = LLMRequest(surface="preflight", rendered=PROBE_PROMPT, tier=route.tier, effort="low", subject=model, worktree=None)
                probes.append((cand.provider, model, adapter, req))
        tasks = [asyncio.create_task(adapter.invoke(req, model)) for _, model, adapter, req in probes]
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
        finally:
            for task in tasks:
                if not task.done():
                    task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
        for (provider, model, adapter, _), result in zip(probes, results, strict=True):
            if isinstance(result, Exception):
                road = f"check {adapter.binary} (clutch/docs/host-{provider}.md)" if adapter.provider.package is None else f"run: clutch provider install {provider}"
                problems.append(f"{provider} model {model!r} failed its probe: {result} -- {road}, or route a model this login serves in config.yaml")
            elif isinstance(result, BaseException):
                raise result
        if not problems:
            self.session.preflight_passed()
        return problems

    async def admitted_call(self, req, *, ticket, call_key, effect, meter=None):
        from clutch.thresh import UnavailableRoute

        route = candidates(self._config, req.tier, req.surface, req.kind)
        index = member_index(call_key)
        if index is not None:
            members = panel_members(self._config, req.tier, req.surface, req.kind)
            if index >= len(members):
                raise ValueError(f"member index {index} exceeds member count {len(members)}")
            assigned = members[index]
            route = (assigned, *(candidate for candidate in route if candidate != assigned))
        # Budget eligibility precedes admission, so a refusal cannot become a
        # provider failure or leave an unmatched Effect intent. Preserve the
        # configured order among candidates that can serve the bounded request.
        affordable = tuple(s for s in route if self._adapters[s.provider.name].within_budget(req))
        if not affordable:
            raise ProviderBudgetExceeded("remaining eval budget cannot admit the declared estimate; rerun the bounded eval")
        route = affordable
        used, queued, cap = self.session.thresh.occupancy(route[0].provider.name)
        estimate = ((used + queued) // cap) * self._timeout

        async def operation(served):
            consumer = meter(served) if meter else None
            capture = None
            if call_key is not None:
                first = route[0].provider.name
                breaker = self.session.thresh.breakers().get(first)
                reason = (
                    "first"
                    if served == route[0]
                    else "failover"
                    if (breaker is not None and breaker.open_until is not None and breaker.open_until > self.session.clock()) or self.session.unavailable(first)[0]
                    else "spill"
                )
                git = Git(
                    self._exec, env=child_env(self._env, self._config), timeout=PREFLIGHT_TIMEOUT_S, commit_lock=CommitLock(self._config.state_dir, clock=self.session.clock, sleep=self.session.sleep)
                )
                capture = CallCapture(call_key, ticket, tuple(s.provider.name for s in route), reason, git, self.session.clock)
            result = await self._invoke(req, served, consumer=consumer, capture=capture)
            if consumer is not None and hasattr(consumer, "complete"):
                consumer.complete()
            return result

        while True:
            result = await self.session.thresh.run(route, ticket=ticket, call_key=call_key, projected_wait_seconds=estimate, effect=effect, operation=operation)
            if not isinstance(result, UnavailableRoute):
                return result.result
            if ticket is not None or result.open_until is None:
                raise ProviderDrought(req.tier, req.surface, result)
            self.session._holds[call_key] = self.session.clock()
            try:
                await self.session.wait_until(result.open_until)
            finally:
                started = self.session._holds.pop(call_key)
                self.session._held_seconds[call_key] = self.session._held_seconds.get(call_key, 0) + max(0, (self.session.clock() - started).total_seconds())

    async def call(self, req: LLMRequest, *, consumer: "EventConsumer | None" = None) -> LLMResult:
        """The raw LLM execution seam; llm_call owns its durable admission boundary."""
        return await self._invoke(req, resolve(self._config, req.tier, req.surface, req.kind), consumer=consumer)

    async def _invoke(self, req, served, *, consumer=None, capture=None):
        self._active = self._adapters[served.provider.name]
        try:
            return await self._active.invoke(req, served.model, capture=capture, **({"consumer": consumer} if consumer is not None else {}))
        finally:
            self._active = None

    def abort_current(self) -> None:
        if self._active is not None:
            self._active.abort()
